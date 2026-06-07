from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class DurationDialog(QDialog):
    def __init__(self, current_minutes: int):
        super().__init__()
        self._selected = int(current_minutes)

        self.setWindowTitle("选择专注时长")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(520, 420)
        self.setStyleSheet("QDialog { background: #f6f7fb; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("专注时长", self)
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        hint = QLabel("点击选择一个预设时长。", self)
        hint.setStyleSheet("color: rgba(0,0,0,0.55);")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(hint)

        content = QWidget(self)
        grid = QGridLayout(content)
        grid.setContentsMargins(6, 6, 6, 6)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        durations = [10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 75, 90]
        col_count = 3
        for i, m in enumerate(durations):
            btn = DurationCard(minutes=m, selected=(m == self._selected), parent=content)
            btn.clicked.connect(lambda _checked=False, minutes=m: self._select(minutes))
            grid.addWidget(btn, i // col_count, i % col_count)

        footer = QHBoxLayout()
        cancel = QPushButton("取消", self)
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
        self.setFixedHeight(74)
        self.setText(f"{int(minutes)} 分钟")
        self.setStyleSheet(
            "QPushButton {"
            "background: rgba(255,255,255,0.92);"
            "border: 1px solid rgba(0,0,0,0.10);"
            "border-radius: 16px;"
            "font-size: 16px;"
            "font-weight: 700;"
            "color: rgba(0,0,0,0.92);"
            "}"
            "QPushButton:hover { border: 1px solid rgba(0,0,0,0.18); }"
            "QPushButton:pressed { background: rgba(245,245,245,1.0); }"
        )
        if selected:
            self.setStyleSheet(
                self.styleSheet()
                + "QPushButton { border: 2px solid rgba(37,99,235,0.65); }"
            )
