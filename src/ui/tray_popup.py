from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class TrayPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.on_toggle: Callable[[], None] | None = None
        self.on_open_main: Callable[[], None] | None = None
        self.on_quit: Callable[[], None] | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setFixedSize(280, 210)
        self.setStyleSheet(
            "QWidget { background-color: rgba(255,255,255,0.96); border: 1px solid rgba(0,0,0,0.10); border-radius: 18px; }"
            "QLabel { color: rgba(0,0,0,0.88); }"
            "QPushButton { background-color: rgba(0,0,0,0.06); color: rgba(0,0,0,0.88); border: 1px solid rgba(0,0,0,0.08); border-radius: 12px; padding: 10px 12px; font-size: 14px; }"
            "QPushButton:hover { background-color: rgba(0,0,0,0.09); }"
            "QPushButton:pressed { background-color: rgba(0,0,0,0.12); }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        self.time_label = QLabel("25:00", self)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setMinimumHeight(60)
        self.time_label.setStyleSheet("font-size: 44px; font-weight: 800;")

        self.type_label = QLabel("默认专注", self)
        self.type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.type_label.setMinimumHeight(28)
        self.type_label.setStyleSheet("font-size: 16px; color: rgba(0,0,0,0.55);")

        actions_row = QHBoxLayout()
        actions_row.setSpacing(12)

        self.toggle_button = QPushButton("开始", self)
        self.toggle_button.setMinimumHeight(40)
        self.toggle_button.clicked.connect(self._handle_toggle)

        self.open_main_button = QPushButton("打开主窗口", self)
        self.open_main_button.setMinimumHeight(40)
        self.open_main_button.clicked.connect(self._handle_open_main)

        actions_row.addWidget(self.toggle_button, 1)
        actions_row.addWidget(self.open_main_button, 1)

        self.quit_button = QPushButton("退出", self)
        self.quit_button.setMinimumHeight(40)
        self.quit_button.clicked.connect(self._handle_quit)

        root.addWidget(self.time_label)
        root.addWidget(self.type_label)
        root.addLayout(actions_row)
        root.addWidget(self.quit_button)
        root.addStretch(1)

    def set_time_text(self, text: str) -> None:
        self.time_label.setText(text)

    def set_focus_type_text(self, text: str) -> None:
        self.type_label.setText(text)

    def set_running(self, running: bool) -> None:
        self.toggle_button.setText("暂停" if running else "开始")

    def focusOutEvent(self, event):
        self.hide()
        super().focusOutEvent(event)

    def _handle_toggle(self) -> None:
        if callable(self.on_toggle):
            self.on_toggle()

    def _handle_open_main(self) -> None:
        if callable(self.on_open_main):
            self.on_open_main()

    def _handle_quit(self) -> None:
        if callable(self.on_quit):
            self.on_quit()
