from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.pomodoro_engine import EngineState, PomodoroEngine
from src.core.settings_store import SettingsStore


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

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(16)

        self.time_label = QLabel("25:00", self)
        self.time_label.setObjectName("Time")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-size: 72px; font-weight: 800;")

        self.phase_label = QLabel("专注", self)
        self.phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phase_label.setStyleSheet("font-size: 16px; font-weight: 650; color: rgba(0,0,0,0.55);")

        self.break_hint = QLabel("", self)
        self.break_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.break_hint.setStyleSheet("font-size: 14px; font-weight: 650; color: rgba(16,185,129,0.95);")
        self.break_hint.hide()

        self.type_row = ChevronRow(title="专注类型", value="学习", parent=self)
        self.type_row.clicked.connect(self._open_type_settings)

        self.duration_row = ChevronRow(title="专注时长", value="25 分钟", parent=self)
        self.duration_row.clicked.connect(self._open_duration_settings)

        actions = QVBoxLayout()
        actions.setSpacing(12)

        self.start_pause_button = QPushButton("开始", self)
        self.start_pause_button.setObjectName("PrimaryButton")
        self.start_pause_button.setFixedHeight(52)
        self.start_pause_button.clicked.connect(self._engine.toggle)
        self.start_pause_button.setStyleSheet(
            "QPushButton#PrimaryButton {"
            "background: #2563EB;"
            "color: white;"
            "border: 1px solid rgba(0,0,0,0.08);"
            "border-radius: 16px;"
            "font-size: 16px;"
            "font-weight: 650;"
            "}"
            "QPushButton#PrimaryButton:hover { background: #1D4ED8; }"
            "QPushButton#PrimaryButton:pressed { background: #1E40AF; }"
        )

        self.reset_button = QPushButton("重置", self)
        self.reset_button.setObjectName("DangerButton")
        self.reset_button.setFixedHeight(52)
        self.reset_button.clicked.connect(self._engine.reset_focus)
        self.reset_button.setStyleSheet(
            "QPushButton#DangerButton {"
            "background: rgba(239,68,68,0.12);"
            "color: rgba(185,28,28,0.95);"
            "border: 1px solid rgba(239,68,68,0.22);"
            "border-radius: 16px;"
            "font-size: 16px;"
            "font-weight: 650;"
            "}"
            "QPushButton#DangerButton:hover { background: rgba(239,68,68,0.16); }"
            "QPushButton#DangerButton:pressed { background: rgba(239,68,68,0.22); }"
        )

        actions.addWidget(self.start_pause_button)
        actions.addWidget(self.reset_button)

        root.addWidget(self.time_label)
        root.addWidget(self.phase_label)
        root.addWidget(self.break_hint)
        root.addWidget(self.type_row)
        root.addWidget(self.duration_row)
        root.addLayout(actions)
        root.addStretch(1)

        self._engine.state_changed.connect(self._on_state_changed)
        self._engine.focus_completed.connect(self._on_focus_completed)
        self._on_state_changed(self._engine.state())

    def _open_type_settings(self) -> None:
        self._on_open_focus_type_settings()

    def _open_duration_settings(self) -> None:
        self._on_open_focus_duration_settings()

    def _on_state_changed(self, state: EngineState) -> None:
        self.time_label.setText(state.time_str)
        if state.phase == "focus":
            self.phase_label.setText("专注")
        elif state.phase == "short_break":
            self.phase_label.setText("短休息")
        else:
            self.phase_label.setText("长休息")
        self.type_row.set_value(state.focus_type)
        self.duration_row.set_value(f"{self._settings.focus_minutes()} 分钟")
        self.type_row.setEnabled(state.phase == "focus")
        self.duration_row.setEnabled(not state.running and state.phase == "focus")

        if state.running:
            self.start_pause_button.setText("暂停")
        else:
            if state.phase == "focus":
                self.start_pause_button.setText("开始")
            elif state.phase == "short_break":
                self.start_pause_button.setText("开始休息")
            else:
                self.start_pause_button.setText("开始长休息")

    def _on_focus_completed(self) -> None:
        QTimer.singleShot(0, self._show_break_hint)

    def _show_break_hint(self) -> None:
        state = self._engine.state()
        if state.phase == "short_break":
            self.break_hint.setText("专注结束，开始短休息")
        elif state.phase == "long_break":
            self.break_hint.setText("专注结束，开始长休息")
        else:
            return
        self.break_hint.show()
        QTimer.singleShot(3500, self.break_hint.hide)


class ChevronRow(QPushButton):
    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent)
        self.setObjectName("ChevronRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(54)
        self.setText("")
        self.setStyleSheet(
            "QPushButton#ChevronRow { background: rgba(255,255,255,0.92); border: 1px solid rgba(0,0,0,0.10); border-radius: 16px; }"
            "QPushButton#ChevronRow:hover { border: 1px solid rgba(0,0,0,0.18); }"
            "QPushButton#ChevronRow:pressed { background: rgba(245,245,245,1.0); }"
            "QLabel { background: transparent; }"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        self.title_label = QLabel(title, self)
        self.title_label.setStyleSheet("color: rgba(0,0,0,0.55); font-size: 14px;")

        self.value_label = QLabel(value, self)
        self.value_label.setStyleSheet("color: rgba(0,0,0,0.92); font-size: 15px; font-weight: 650;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.chevron = QLabel(">", self)
        self.chevron.setStyleSheet("color: rgba(0,0,0,0.35); font-size: 16px; font-weight: 700;")

        layout.addWidget(self.title_label, 0)
        layout.addStretch(1)
        layout.addWidget(self.value_label, 0)
        layout.addWidget(self.chevron, 0)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)
