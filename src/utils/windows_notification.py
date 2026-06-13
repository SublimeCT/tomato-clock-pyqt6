from __future__ import annotations

import ctypes
import html
import shutil
import subprocess
import sys

WINDOWS_APP_USER_MODEL_ID = "SublimeCT.TomatoClock"


def configure_windows_app_id() -> None:
    """为 Windows 进程设置稳定的 AppUserModelID。"""

    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(WINDOWS_APP_USER_MODEL_ID)
    except Exception:
        return


def show_windows_notification(title: str, message: str) -> bool:
    """优先使用 Windows 原生 toast，失败时返回 False 交由上层兜底。"""

    if sys.platform != "win32":
        return False

    powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
    if not powershell:
        return False

    xml_title = html.escape(str(title), quote=False)
    xml_message = html.escape(str(message), quote=False)
    script = f"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] > $null
$xml = @'
<toast>
  <visual>
    <binding template="ToastGeneric">
      <text>{xml_title}</text>
      <text>{xml_message}</text>
    </binding>
  </visual>
</toast>
'@
$doc = New-Object Windows.Data.Xml.Dom.XmlDocument
$doc.LoadXml($xml)
$toast = [Windows.UI.Notifications.ToastNotification]::new($doc)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{WINDOWS_APP_USER_MODEL_ID}')
$notifier.Show($toast)
"""
    popen_kwargs: dict = {
        "args": [powershell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
        "check": False,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        popen_kwargs["startupinfo"] = startupinfo
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    result = subprocess.run(**popen_kwargs)
    return result.returncode == 0
