from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from src.ui.ui_theme import TEXT, apply_fixed_policy


class UpdateNoticeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_fixed_policy(self)
        self._release_url = ""
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide_notice)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        self._label = QLabel(self)
        self._label.setWordWrap(True)
        self._label.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 600; background: transparent;")

        self._download_button = QPushButton("前往下载", self)
        self._download_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._download_button.clicked.connect(self._open_release_page)
        self._download_button.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; border: 0; border-radius: 10px;"
            "font-size: 12px; font-weight: 700; padding: 8px 12px; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )

        self._close_button = QPushButton("关闭", self)
        self._close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_button.clicked.connect(self.hide_notice)
        self._close_button.setStyleSheet(
            "QPushButton { background: rgba(37,99,235,0.08); color: #1D4ED8; border: 0; border-radius: 10px;"
            "font-size: 12px; font-weight: 600; padding: 8px 10px; }"
            "QPushButton:hover { background: rgba(37,99,235,0.14); }"
        )

        layout.addWidget(self._label, 1)
        layout.addWidget(self._download_button, 0)
        layout.addWidget(self._close_button, 0)

        self.setStyleSheet(
            "UpdateNoticeWidget { background: rgba(37,99,235,0.08); border: 1px solid rgba(37,99,235,0.18);"
            "border-radius: 16px; }"
        )
        self.hide()

    def show_notice(self, latest_version: str, release_url: str) -> None:
        self._release_url = str(release_url).strip()
        self._label.setText(f"发现新版本 v{latest_version}。建议前往 GitHub Releases 下载最新稳定构建。")
        self.show()
        self._hide_timer.start(5000)

    def hide_notice(self) -> None:
        self._hide_timer.stop()
        self.hide()

    def _open_release_page(self) -> None:
        if self._release_url:
            QDesktopServices.openUrl(QUrl(self._release_url))
        self.hide_notice()
