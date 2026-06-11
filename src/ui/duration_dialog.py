from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.ui.ui_theme import ACCENT, BG, BORDER, MUTED, TEXT, apply_fixed_policy, apply_panel_policy, rgba


class DurationDialog(QDialog):
    def __init__(self, current_minutes: int):
        super().__init__()
        self._selected = int(current_minutes)

        self.setWindowTitle("选择专注时长")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(480, 420)
        self.setStyleSheet(f"QDialog {{ background: {BG}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("专注时长", self)
        apply_fixed_policy(title, 28)
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT};")
        hint = QLabel("点击选择一个预设时长。", self)
        apply_fixed_policy(hint, 24)
        hint.setStyleSheet(f"color: {MUTED};")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(hint)

        content = QWidget(self)
        apply_panel_policy(content)
        content.setStyleSheet(f"background: white; border: 1px solid rgba(0,0,0,0.06); border-radius: 18px;")
        grid = QGridLayout(content)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        durations = [10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 75, 90]
        col_count = 3
        for i, m in enumerate(durations):
            btn = DurationCard(minutes=m, selected=(m == self._selected), parent=content)
            btn.clicked.connect(lambda _checked=False, minutes=m: self._select(minutes))
            grid.addWidget(btn, i // col_count, i % col_count)

        footer = QHBoxLayout()
        cancel = QPushButton("取消", self)
        apply_fixed_policy(cancel, 40)
        cancel.setStyleSheet(
            f"QPushButton {{ background: white; border: 1px solid {BORDER}; border-radius: 8px; color: {TEXT}; padding: 0 24px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {rgba(ACCENT, 0.08)}; color: {ACCENT}; }}"
        )
        cancel.clicked.connect(self.reject)
        footer.addStretch(1)
        footer.addWidget(cancel)

        root.addLayout(header)
        root.addWidget(content, 1)
        root.addLayout(footer)

    def selected_minutes(self) -> int:
        return int(self._selected)

    def _select(self, minutes: int) -> None:
        self._selected = int(minutes)
        self.accept()


class DurationCard(QPushButton):
    def __init__(self, minutes: int, selected: bool, parent=None):
        super().__init__(parent)
        self.setCheckable(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_fixed_policy(self, 84)
        self.setText(f"{int(minutes)} 分钟")
        self.setStyleSheet(
            f"QPushButton {{ background: white; border: 2px solid rgba(0,0,0,0.06); border-radius: 14px; font-size: 18px; font-weight: 700; color: {TEXT}; }}"
            f"QPushButton:hover {{ border: 2px solid {BORDER}; background: {BG}; }}"
        )
        if selected:
            self.setStyleSheet(
                self.styleSheet()
                + f"QPushButton {{ border: 2px solid {ACCENT}; background: {rgba(ACCENT, 0.08)}; color: {ACCENT}; }}"
            )
