from __future__ import annotations

import tomllib
from typing import cast

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

REMOTE_VERSION_URL = (
    "https://raw.githubusercontent.com/SublimeCT/tomato-clock-pyqt6/refs/heads/main/pyproject.toml"
)


def _extract_version(payload: bytes) -> str:
    try:
        data = tomllib.loads(payload.decode("utf-8"))
    except Exception:
        return ""
    version = data.get("project", {}).get("version", "")
    return version.strip() if isinstance(version, str) else ""


class AppUpdateChecker(QObject):
    update_available = pyqtSignal(str, str)

    def __init__(
        self,
        current_version: str,
        repository_url: str,
        *,
        version_url: str = REMOTE_VERSION_URL,
        timeout_ms: int = 4000,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._current_version = str(current_version).strip()
        self._version_url = str(version_url).strip()
        self._release_url = f"{str(repository_url).rstrip('/')}/releases"
        self._timeout_ms = max(1000, int(timeout_ms))
        self._manager = QNetworkAccessManager(self)
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._abort_active_reply)
        self._reply: QNetworkReply | None = None

    def start(self) -> None:
        if self._reply is not None or not self._version_url:
            return
        request = QNetworkRequest(QUrl(self._version_url))
        request.setTransferTimeout(self._timeout_ms)
        request.setHeader(
            QNetworkRequest.KnownHeaders.UserAgentHeader,
            f"TomatoClock/{self._current_version or '0.0.0'}",
        )
        reply = cast(QNetworkReply, self._manager.get(request))
        self._reply = reply
        reply.finished.connect(self._on_reply_finished)
        self._timeout_timer.start(self._timeout_ms + 300)

    def _abort_active_reply(self) -> None:
        if self._reply is not None and self._reply.isRunning():
            self._reply.abort()

    def _on_reply_finished(self) -> None:
        reply = self._reply
        self._reply = None
        self._timeout_timer.stop()
        if reply is None:
            return
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                return
            latest_version = _extract_version(reply.readAll().data())
            if not latest_version or latest_version == self._current_version:
                return
            self.update_available.emit(latest_version, self._release_url)
        finally:
            reply.deleteLater()
