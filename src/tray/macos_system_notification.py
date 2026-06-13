from __future__ import annotations
# pyright: reportMissingImports=false, reportAttributeAccessIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false

import subprocess
import threading
from uuid import uuid4

from Foundation import NSBundle, NSObject
from UserNotifications import (
    UNAuthorizationOptionAlert,
    UNAuthorizationOptionBadge,
    UNAuthorizationOptionSound,
    UNAuthorizationStatusAuthorized,
    UNAuthorizationStatusEphemeral,
    UNAuthorizationStatusProvisional,
    UNMutableNotificationContent,
    UNNotificationPresentationOptionAlert,
    UNNotificationPresentationOptionBadge,
    UNNotificationPresentationOptionSound,
    UNNotificationRequest,
    UNUserNotificationCenter,
)


class _NotificationDelegate(NSObject):
    def userNotificationCenter_willPresentNotification_withCompletionHandler_(
        self, _center, _notification, completion_handler
    ):
        completion_handler(
            UNNotificationPresentationOptionAlert
            | UNNotificationPresentationOptionSound
            | UNNotificationPresentationOptionBadge
        )


class MacSystemNotificationCenter:
    """使用 Apple UserNotifications 框架发送 macOS 系统通知。"""

    def __init__(self):
        bundle = NSBundle.mainBundle()
        bundle_id = bundle.bundleIdentifier()
        bundle_path = str(bundle.bundlePath() or "")
        self._use_user_notifications = bool(bundle_id) and bundle_path.endswith(".app")
        self._center = None
        self._delegate = None
        if self._use_user_notifications:
            self._center = UNUserNotificationCenter.currentNotificationCenter()
            self._delegate = _NotificationDelegate.alloc().init()
            self._center.setDelegate_(self._delegate)

    def show_message(self, title: str, message: str) -> None:
        if not self._use_user_notifications:
            script = (
                f'display notification "{self._escape_osascript(message)}" '
                f'with title "{self._escape_osascript(title)}"'
            )
            subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return

        granted = self._ensure_authorized()
        if not granted:
            return

        content = UNMutableNotificationContent.alloc().init()
        content.setTitle_(str(title))
        content.setBody_(str(message))
        content.setSound_(None)

        identifier = f"tomato-clock-{uuid4()}"
        request = UNNotificationRequest.requestWithIdentifier_content_trigger_(identifier, content, None)
        if self._center is None:
            return
        self._center.addNotificationRequest_withCompletionHandler_(request, self._on_add_request)

    def _ensure_authorized(self) -> bool:
        if self._center is None:
            return False
        center = self._center
        event = threading.Event()
        result = {"granted": False, "status": "unknown"}

        def _settings_handler(settings):
            status = int(settings.authorizationStatus())
            result["status"] = status
            if status in (
                int(UNAuthorizationStatusAuthorized),
                int(UNAuthorizationStatusProvisional),
                int(UNAuthorizationStatusEphemeral),
            ):
                result["granted"] = True
                event.set()
                return

            def _auth_handler(granted, error):
                result["granted"] = bool(granted)
                result["error"] = "" if error is None else str(error)
                event.set()

            center.requestAuthorizationWithOptions_completionHandler_(
                UNAuthorizationOptionAlert | UNAuthorizationOptionBadge | UNAuthorizationOptionSound,
                _auth_handler,
            )

        center.getNotificationSettingsWithCompletionHandler_(_settings_handler)
        event.wait(2.0)
        return bool(result.get("granted"))

    def _on_add_request(self, _error) -> None:
        return None

    def _escape_osascript(self, value: str) -> str:
        return str(value).replace("\\", "\\\\").replace('"', '\\"')
