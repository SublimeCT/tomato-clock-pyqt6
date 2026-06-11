from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from src.ui.ui_theme import MUTED, apply_fixed_policy


class AppTitleBar(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("AppTitleBar")
        apply_fixed_policy(self, 52)
        self.setStyleSheet(
            f"QWidget#AppTitleBar {{ background: transparent; }}"
            f"QLabel#title {{ color: {MUTED}; font-size: 13px; font-weight: 600; }}"
        )

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 0, 20, 0)
        root.setSpacing(0)

        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.title_label, 1)

    def set_title(self, title: str) -> None:
        self.title_label.setText(str(title))
