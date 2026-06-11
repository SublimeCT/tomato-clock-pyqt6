from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from src.ui.ui_theme import ACCENT, BG, BORDER, MUTED, TEXT, apply_fixed_policy, rgba


class StepperControl(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, minimum: int, maximum: int, value: int, unit: str, parent=None):
        super().__init__(parent)
        self._minimum = int(minimum)
        self._maximum = int(maximum)
        self._value = int(value)
        self.setObjectName("StepperControl")
        apply_fixed_policy(self, 36)
        self.setStyleSheet(
            f"QWidget#StepperControl {{ background: transparent; }}"
            f"QWidget#StepperBox {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 10px; }}"
            f"QPushButton#StepperButton {{ border: 0; background: transparent; color: {TEXT}; font-size: 18px; font-weight: 500; }}"
            f"QPushButton#StepperButton:hover {{ background: {rgba(ACCENT, 0.08)}; color: {ACCENT}; }}"
            f"QLabel#StepperValue {{ color: {TEXT}; font-size: 16px; font-weight: 600; }}"
            f"QLabel#StepperUnit {{ color: {MUTED}; font-size: 12px; }}"
        )

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        box = QWidget(self)
        box.setObjectName("StepperBox")
        apply_fixed_policy(box, 36)
        box.setFixedWidth(116)
        box_row = QHBoxLayout(box)
        box_row.setContentsMargins(0, 0, 0, 0)
        box_row.setSpacing(0)

        self.minus_btn = QPushButton("−", box)
        self.minus_btn.setObjectName("StepperButton")
        apply_fixed_policy(self.minus_btn, 36)
        self.minus_btn.setFixedWidth(36)
        self.minus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.minus_btn.clicked.connect(lambda: self.set_value(self._value - 1))

        self.value_label = QLabel("", box)
        self.value_label.setObjectName("StepperValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        apply_fixed_policy(self.value_label, 36)
        self.value_label.setFixedWidth(44)
        self.value_label.setStyleSheet(
            f"QLabel#StepperValue {{ color: {TEXT}; font-size: 16px; font-weight: 600; border-left: 1px solid {BORDER}; border-right: 1px solid {BORDER}; }}"
        )

        self.plus_btn = QPushButton("+", box)
        self.plus_btn.setObjectName("StepperButton")
        apply_fixed_policy(self.plus_btn, 36)
        self.plus_btn.setFixedWidth(36)
        self.plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.plus_btn.clicked.connect(lambda: self.set_value(self._value + 1))

        self.unit_label = QLabel(unit, self)
        self.unit_label.setObjectName("StepperUnit")
        apply_fixed_policy(self.unit_label, 20)

        box_row.addWidget(self.minus_btn)
        box_row.addWidget(self.value_label)
        box_row.addWidget(self.plus_btn)
        root.addWidget(box, 0)
        root.addWidget(self.unit_label, 0)
        self.set_value(self._value, emit=False)

    def value(self) -> int:
        return self._value

    def set_value(self, value: int, *, emit: bool = True) -> None:
        bounded = max(self._minimum, min(self._maximum, int(value)))
        if bounded == self._value and emit:
            return
        self._value = bounded
        self.value_label.setText(str(self._value))
        self.minus_btn.setEnabled(self._value > self._minimum)
        self.plus_btn.setEnabled(self._value < self._maximum)
        if emit:
            self.valueChanged.emit(self._value)
