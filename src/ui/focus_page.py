from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.core.pomodoro_engine import EngineState, PomodoroEngine
from src.core.settings_store import SettingsStore
from src.ui.focus_widgets import ChevronRow, SessionDotsWidget, TimerRingWidget
from src.ui.ui_theme import ACCENT, ACCENT_HOVER, SUCCESS, WARN, apply_fixed_policy, rgba


class FocusPage(QWidget):
    def __init__(
        self,
        engine: PomodoroEngine,
        settings: SettingsStore,
        on_open_focus_type_settings: Callable[[], None],
        on_open_focus_duration_settings: Callable[[], None],
    ):
        super().__init__()
        self._engine = engine
        self._settings = settings
        self._on_open_focus_type_settings = on_open_focus_type_settings
        self._on_open_focus_duration_settings = on_open_focus_duration_settings
        self.setStyleSheet("FocusPage { background: #FDF6F0; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 24)
        root.setSpacing(0)

        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 24, 24, 0)
        body_layout.setSpacing(16)
        body_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.session_dots = SessionDotsWidget(self)
        self.timer_ring = TimerRingWidget(self)

        self.break_hint = QLabel("", self)
        apply_fixed_policy(self.break_hint, 44)
        self.break_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.break_hint.setStyleSheet(
            f"background: {rgba(SUCCESS, 0.10)}; color: {SUCCESS}; border-radius: 12px;"
            "font-size: 14px; font-weight: 600;"
        )
        self.break_hint.hide()

        self.type_row = ChevronRow("专注类型", "学习", self)
        self.type_row.clicked.connect(self._open_type_settings)
        self.duration_row = ChevronRow("专注时长", "25 分钟", self)
        self.duration_row.clicked.connect(self._open_duration_settings)

        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.start_pause_button = QPushButton("开始", self)
        apply_fixed_policy(self.start_pause_button, 52)
        self.start_pause_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_pause_button.clicked.connect(self._engine.toggle)

        self.reset_button = QPushButton("↺", self)
        self.reset_button.setToolTip("重置")
        apply_fixed_policy(self.reset_button, 52)
        self.reset_button.setFixedWidth(52)
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.clicked.connect(self._engine.reset_focus)

        self._apply_action_styles(False, False)
        action_row.addWidget(self.start_pause_button, 1)
        action_row.addWidget(self.reset_button, 0)

        body_layout.addWidget(self.session_dots, 0, Qt.AlignmentFlag.AlignHCenter)
        body_layout.addWidget(self.timer_ring, 0, Qt.AlignmentFlag.AlignHCenter)
        body_layout.addWidget(self.break_hint)
        body_layout.addWidget(self.type_row)
        body_layout.addWidget(self.duration_row)
        body_layout.addLayout(action_row)
        body_layout.addStretch(1)
        root.addWidget(body, 1)

        self._engine.state_changed.connect(self._on_state_changed)
        self._engine.focus_completed.connect(self._on_focus_completed)
        self._on_state_changed(self._engine.state())

    def _apply_action_styles(self, running: bool, break_mode: bool) -> None:
        primary = WARN if running else SUCCESS if break_mode else ACCENT
        primary_hover = "#E8943A" if running else "#23867B" if break_mode else ACCENT_HOVER
        self.start_pause_button.setStyleSheet(
            f"QPushButton {{ background: {primary}; color: white; border: 0; border-radius: 18px;"
            "font-size: 17px; font-weight: 700; padding: 0 18px; }"
            f"QPushButton:hover {{ background: {primary_hover}; }}"
        )
        self.reset_button.setStyleSheet(
            "QPushButton { background: white; color: #4A4A5A; border: 1px solid rgba(0,0,0,0.08);"
            "border-radius: 12px; font-size: 20px; font-weight: 700; }"
            f"QPushButton:hover {{ background: {rgba(ACCENT, 0.08)}; color: {ACCENT}; }}"
        )

    def _open_type_settings(self) -> None:
        self._on_open_focus_type_settings()

    def _open_duration_settings(self) -> None:
        self._on_open_focus_duration_settings()

    def _on_state_changed(self, state: EngineState) -> None:
        phase_text = "专注" if state.phase == "focus" else "短休息" if state.phase == "short_break" else "长休息"
        self.timer_ring.set_content(state.time_str, phase_text)
        self.timer_ring.set_running(state.running, state.phase != "focus")
        self.timer_ring.set_progress(state.remaining_seconds, state.total_seconds)

        colors = self._settings.focus_type_colors()
        self.type_row.set_value(state.focus_type, colors.get(state.focus_type, "#4F46E5"))
        self.duration_row.set_value(f"{self._settings.focus_minutes()} 分钟", "#8C8C9A")
        self.type_row.setEnabled(state.phase == "focus")
        self.duration_row.setEnabled(not state.running and state.phase == "focus")

        completed = state.completed_focus_count % max(1, state.long_break_every)
        self.session_dots.set_progress(completed, state.long_break_every)

        if state.running:
            self.start_pause_button.setText("暂停")
        elif state.phase == "focus":
            self.start_pause_button.setText("开始")
        else:
            self.start_pause_button.setText("开始休息")
        self._apply_action_styles(state.running, state.phase != "focus")

    def _on_focus_completed(self) -> None:
        QTimer.singleShot(0, self._show_break_hint)

    def _show_break_hint(self) -> None:
        state = self._engine.state()
        if state.phase == "short_break":
            self.break_hint.setText("专注阶段完成，休息一下吧")
        elif state.phase == "long_break":
            self.break_hint.setText("完成多个番茄周期，开始长休息")
        else:
            return
        self.break_hint.show()
        QTimer.singleShot(3500, self.break_hint.hide)
