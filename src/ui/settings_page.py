from __future__ import annotations

from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.pomodoro_engine import PomodoroEngine
from src.core.settings_store import SettingsStore


class SettingsPage(QWidget):
    def __init__(self, engine: PomodoroEngine, settings: SettingsStore):
        super().__init__()
        self._engine = engine
        self._settings = settings

        self.setStyleSheet(
            "QGroupBox { border: 1px solid rgba(0,0,0,0.08); border-radius: 14px; background: rgba(255,255,255,0.70); margin-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: rgba(0,0,0,0.65); }"
            "QLabel { color: rgba(0,0,0,0.75); }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        durations_group = QGroupBox("时长", self)
        durations_form = QFormLayout(durations_group)

        self.focus_spin = QSpinBox(self)
        self.focus_spin.setRange(1, 180)
        self.focus_spin.setValue(self._settings.focus_minutes())
        self.focus_spin.setSuffix(" 分钟")
        self.focus_spin.valueChanged.connect(self._on_focus_changed)

        self.short_break_spin = QSpinBox(self)
        self.short_break_spin.setRange(1, 60)
        self.short_break_spin.setValue(self._settings.short_break_minutes())
        self.short_break_spin.setSuffix(" 分钟")
        self.short_break_spin.valueChanged.connect(self._on_short_break_changed)

        self.long_break_spin = QSpinBox(self)
        self.long_break_spin.setRange(1, 90)
        self.long_break_spin.setValue(self._settings.long_break_minutes())
        self.long_break_spin.setSuffix(" 分钟")
        self.long_break_spin.valueChanged.connect(self._on_long_break_changed)

        self.long_break_every_spin = QSpinBox(self)
        self.long_break_every_spin.setRange(1, 12)
        self.long_break_every_spin.setValue(self._settings.long_break_every())
        self.long_break_every_spin.setSuffix(" 次")
        self.long_break_every_spin.valueChanged.connect(self._on_long_break_every_changed)

        durations_form.addRow("默认专注时长", self.focus_spin)
        durations_form.addRow("短休息时长", self.short_break_spin)
        durations_form.addRow("长休息时长", self.long_break_spin)
        durations_form.addRow("长休息所需次数", self.long_break_every_spin)

        about_group = QGroupBox("关于", self)
        about_layout = QVBoxLayout(about_group)
        about_layout.addWidget(QLabel("Tomato Clock (PyQt6)", about_group))
        about_layout.addWidget(QLabel("托盘番茄钟 / 专注 / 统计", about_group))

        root.addWidget(durations_group)
        root.addWidget(about_group)
        root.addStretch(1)

    def _on_focus_changed(self, value: int) -> None:
        self._engine.set_focus_minutes(value)

    def _on_short_break_changed(self, value: int) -> None:
        self._engine.set_short_break_minutes(value)

    def _on_long_break_changed(self, value: int) -> None:
        self._engine.set_long_break_minutes(value)

    def _on_long_break_every_changed(self, value: int) -> None:
        self._engine.set_long_break_every(value)
