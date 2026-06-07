from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy, QWidget


class BottomNavBar(QWidget):
    current_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: list[QPushButton] = []
        self._current = 0

        self.setFixedHeight(72)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            "BottomNavBar { background: rgba(255,255,255,0.92); border-top: 1px solid rgba(0,0,0,0.10); }"
            "QPushButton { border: 0; background: transparent; color: rgba(0,0,0,0.60); font-size: 14px; font-weight: 600; }"
            "QPushButton:hover { background: rgba(0,0,0,0.06); }"
            "QPushButton:checked { background: rgba(0,0,0,0.10); color: rgba(0,0,0,0.92); }"
        )

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(10)

    def set_items(self, labels: list[str]) -> None:
        for b in self._buttons:
            self._layout.removeWidget(b)
            b.deleteLater()
        self._buttons = []

        for idx, label in enumerate(labels):
            btn = QPushButton(label, self)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.clicked.connect(lambda _checked=False, i=idx: self.set_current_index(i))
            self._layout.addWidget(btn, 1)
            self._buttons.append(btn)

        self.set_current_index(0)

    def set_current_index(self, index: int) -> None:
        if index < 0 or index >= len(self._buttons):
            return
        self._current = index
        for i, b in enumerate(self._buttons):
            b.setChecked(i == index)
        self.current_changed.emit(index)

