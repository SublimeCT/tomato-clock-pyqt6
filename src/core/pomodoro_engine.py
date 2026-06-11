from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, QTime, pyqtSignal

from src.core.session_store import SessionStore
from src.core.settings_store import SettingsStore


@dataclass(frozen=True)
class EngineState:
    phase: str
    running: bool
    time_str: str
    focus_type: str
    remaining_seconds: int
    total_seconds: int
    completed_focus_count: int
    long_break_every: int


@dataclass(frozen=True)
class PhaseFinishedEvent:
    finished_phase: str
    next_phase: str
    focus_type: str


class PomodoroEngine(QObject):
    state_changed = pyqtSignal(object)
    focus_completed = pyqtSignal()
    phase_finished = pyqtSignal(object)

    def __init__(self, settings: SettingsStore, sessions: SessionStore):
        super().__init__()
        self._settings = settings
        self._sessions = sessions

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._phase = "focus"
        self._running = False
        self._duration = QTime(0, self._settings.focus_minutes(), 0)
        self._focus_type = self._settings.default_focus_type()
        self._focus_started_at: datetime | None = None
        self._completed_focus_count = 0

        self._emit_state()

    def state(self) -> EngineState:
        total_seconds = (
            self._settings.focus_minutes() * 60
            if self._phase == "focus"
            else self._settings.short_break_minutes() * 60
            if self._phase == "short_break"
            else self._settings.long_break_minutes() * 60
        )
        return EngineState(
            phase=self._phase,
            running=self._running,
            time_str=self._duration.toString("mm:ss"),
            focus_type=self._focus_type,
            remaining_seconds=QTime(0, 0, 0).secsTo(self._duration),
            total_seconds=int(total_seconds),
            completed_focus_count=int(self._completed_focus_count),
            long_break_every=int(self._settings.long_break_every()),
        )

    def set_focus_type(self, focus_type: str) -> None:
        self._focus_type = focus_type
        self._settings.set_default_focus_type(focus_type)
        self._emit_state()

    def set_focus_minutes(self, minutes: int) -> None:
        self._settings.set_focus_minutes(minutes)
        if self._phase == "focus" and not self._running:
            self._duration = QTime(0, int(minutes), 0)
            self._emit_state()

    def set_short_break_minutes(self, minutes: int) -> None:
        self._settings.set_short_break_minutes(minutes)

    def set_long_break_minutes(self, minutes: int) -> None:
        self._settings.set_long_break_minutes(minutes)

    def set_long_break_every(self, count: int) -> None:
        self._settings.set_long_break_every(count)

    def toggle(self) -> None:
        if self._running:
            self.pause()
        else:
            self.start()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        if self._phase == "focus" and self._focus_started_at is None:
            self._focus_started_at = datetime.now()
        self._timer.start(1000)
        self._emit_state()

    def pause(self) -> None:
        if not self._running:
            return
        self._running = False
        self._timer.stop()
        self._emit_state()

    def reset_focus(self) -> None:
        self.pause()
        self._phase = "focus"
        self._duration = QTime(0, self._settings.focus_minutes(), 0)
        self._focus_started_at = None
        self._emit_state()

    def _tick(self) -> None:
        if self._duration <= QTime(0, 0, 0):
            self._on_phase_finished()
            return
        self._duration = self._duration.addSecs(-1)
        self._emit_state()

    def _on_phase_finished(self) -> None:
        self._timer.stop()
        self._running = False
        finished_phase = self._phase

        if self._phase == "focus":
            started_at = self._focus_started_at or datetime.now()
            completed_at = datetime.now()
            self._sessions.add_session(
                focus_type=self._focus_type,
                minutes=self._settings.focus_minutes(),
                started_at=started_at,
                completed_at=completed_at,
            )
            self._focus_started_at = None
            self._completed_focus_count += 1
            self.focus_completed.emit()

            if self._completed_focus_count % max(1, self._settings.long_break_every()) == 0:
                self._phase = "long_break"
                self._duration = QTime(0, self._settings.long_break_minutes(), 0)
            else:
                self._phase = "short_break"
                self._duration = QTime(0, self._settings.short_break_minutes(), 0)
        else:
            self._phase = "focus"
            self._duration = QTime(0, self._settings.focus_minutes(), 0)

        self.phase_finished.emit(
            PhaseFinishedEvent(
                finished_phase=finished_phase,
                next_phase=self._phase,
                focus_type=self._focus_type,
            )
        )
        self._emit_state()

    def _emit_state(self) -> None:
        self.state_changed.emit(self.state())
