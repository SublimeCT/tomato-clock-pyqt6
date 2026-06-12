from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, QTime, pyqtSignal

from src.core.session_store import SessionStore
from src.core.settings_models import FocusTemplate
from src.core.settings_store import SettingsStore


@dataclass(frozen=True)
class EngineState:
    phase: str
    running: bool
    time_str: str
    focus_type: str
    template_id: str
    remaining_seconds: int
    total_seconds: int
    completed_focus_count: int
    long_break_every: int


@dataclass(frozen=True)
class PhaseFinishedEvent:
    finished_phase: str
    next_phase: str
    focus_type: str
    prompt_message: str


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
        self._template_id = self._settings.active_template_id()
        self._focus_started_at: datetime | None = None
        self._completed_focus_count = 0

        self._emit_state()

    def state(self) -> EngineState:
        total_seconds = (
            self._focus_minutes() * 60
            if self._phase == "focus"
            else self._short_break_minutes() * 60
            if self._phase == "short_break"
            else self._long_break_minutes() * 60
        )
        return EngineState(
            phase=self._phase,
            running=self._running,
            time_str=self._duration.toString("mm:ss"),
            focus_type=self._focus_type,
            template_id=self._template_id,
            remaining_seconds=QTime(0, 0, 0).secsTo(self._duration),
            total_seconds=int(total_seconds),
            completed_focus_count=int(self._completed_focus_count),
            long_break_every=int(self._long_break_every()),
        )

    def set_focus_type(self, focus_type: str) -> None:
        self._focus_type = focus_type
        self._settings.set_default_focus_type(focus_type)
        self._emit_state()

    def set_focus_minutes(self, minutes: int) -> None:
        self._settings.set_focus_minutes(minutes)
        self._clear_active_template()
        if self._phase == "focus" and not self._running:
            self._duration = QTime(0, int(minutes), 0)
            self._emit_state()

    def set_short_break_minutes(self, minutes: int) -> None:
        self._settings.set_short_break_minutes(minutes)
        self._clear_active_template()
        if self._phase == "short_break" and not self._running:
            self._duration = QTime(0, int(minutes), 0)
        if not self._running:
            self._emit_state()

    def set_long_break_minutes(self, minutes: int) -> None:
        self._settings.set_long_break_minutes(minutes)
        self._clear_active_template()
        if self._phase == "long_break" and not self._running:
            self._duration = QTime(0, int(minutes), 0)
        if not self._running:
            self._emit_state()

    def set_long_break_every(self, count: int) -> None:
        self._settings.set_long_break_every(count)
        self._clear_active_template()
        if not self._running:
            self._emit_state()

    def apply_template(self, template: FocusTemplate) -> None:
        if self._running or self._phase != "focus":
            return
        self._template_id = template.id
        self._settings.set_active_template_id(template.id)
        self._duration = QTime(0, template.focus_minutes, 0)
        self._emit_state()

    def clear_template(self) -> None:
        if self._running or self._phase != "focus":
            return
        self._clear_active_template()
        self._duration = QTime(0, self._settings.focus_minutes(), 0)
        self._emit_state()

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
        self._duration = QTime(0, self._focus_minutes(), 0)
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
                minutes=self._focus_minutes(),
                started_at=started_at,
                completed_at=completed_at,
                template_name=self._active_template_name(),
            )
            self._focus_started_at = None
            self._completed_focus_count += 1
            self.focus_completed.emit()

            if self._completed_focus_count % max(1, self._long_break_every()) == 0:
                self._phase = "long_break"
                self._duration = QTime(0, self._long_break_minutes(), 0)
            else:
                self._phase = "short_break"
                self._duration = QTime(0, self._short_break_minutes(), 0)
        else:
            self._phase = "focus"
            self._duration = QTime(0, self._focus_minutes(), 0)

        self.phase_finished.emit(
            PhaseFinishedEvent(
                finished_phase=finished_phase,
                next_phase=self._phase,
                focus_type=self._focus_type,
                prompt_message=self._phase_prompt(finished_phase),
            )
        )
        self._emit_state()

    def _emit_state(self) -> None:
        self.state_changed.emit(self.state())

    def _clear_active_template(self) -> None:
        if not self._template_id:
            return
        self._template_id = ""
        self._settings.set_active_template_id("")

    def _active_template_name(self) -> str:
        template = self._active_template()
        return template.name if template is not None else ""

    def _active_template(self) -> FocusTemplate | None:
        return self._settings.template_by_id(self._template_id) if self._template_id else None

    def _focus_minutes(self) -> int:
        template = self._active_template()
        return template.focus_minutes if template is not None else self._settings.focus_minutes()

    def _short_break_minutes(self) -> int:
        template = self._active_template()
        return template.short_break_minutes if template is not None else self._settings.short_break_minutes()

    def _long_break_minutes(self) -> int:
        template = self._active_template()
        return template.long_break_minutes if template is not None else self._settings.long_break_minutes()

    def _long_break_every(self) -> int:
        template = self._active_template()
        return template.rounds if template is not None else self._settings.long_break_every()

    def _phase_prompt(self, finished_phase: str) -> str:
        if finished_phase == "focus":
            return self._settings.pick_focus_end_prompt()
        return self._settings.pick_rest_end_prompt()
