from __future__ import annotations

import shutil
import subprocess
import sys

from src.utils.icon_loader import resolve_asset_path


def show_linux_notification(title: str, message: str) -> bool:
    """使用 notify-send 作为 Linux 系统通知兜底。"""

    if sys.platform != "linux":
        return False

    notify_send = shutil.which("notify-send")
    if not notify_send:
        return False

    command = [notify_send, "-a", "番茄专注", str(title), str(message)]
    icon_path = resolve_asset_path("app-icon.png")
    if icon_path:
        command.extend(["-i", icon_path])
    subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True
