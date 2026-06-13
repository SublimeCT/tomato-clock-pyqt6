from __future__ import annotations

import sys

from PyQt6.QtCore import QByteArray, QBuffer, QPoint, QTimer, Qt
from PyQt6.QtGui import QCursor, QFont, QFontMetrics, QGuiApplication, QIcon, QImage, QPainter, QPalette, QPixmap
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from src.core.pomodoro_engine import EngineState, PhaseFinishedEvent, PomodoroEngine
from src.core.settings_store import SettingsStore
from src.ui.main_window import MainWindow
from src.ui.tray_popup import TrayPopup
from src.utils.system_notification_fallback import show_linux_notification
from src.utils.windows_notification import show_windows_notification
if sys.platform == "darwin":
    from src.tray.macos_system_notification import MacSystemNotificationCenter
    from src.tray.macos_status_item import MacStatusItem


class TrayController:
    def __init__(self, engine: PomodoroEngine, settings: SettingsStore, main_window: MainWindow, app_icon: QIcon):
        self._engine = engine
        self._settings = settings
        self._main_window = main_window
        self._app_icon = app_icon
        self._tray_base_icon = self._make_tray_color_icon(self._app_icon)
        self._use_macos_status_item = sys.platform == "darwin"
        self._popup_ready = False
        self._last_focus_type: str | None = None
        self._focus_type_colors = self._settings.focus_type_colors()

        self._tray: QSystemTrayIcon | None = None
        self._mac_item: MacStatusItem | None = None
        self._mac_notification: MacSystemNotificationCenter | None = None
        if self._use_macos_status_item:
            self._mac_item = MacStatusItem()
            self._mac_notification = MacSystemNotificationCenter()
            self._mac_item.set_click_callback(self.show_popup)
            self._mac_item.set_image_scaling_proportionally_down()
            png_bytes = self._icon_to_png_bytes(self._tray_base_icon, size=18, dpr_override=1.0)
            if png_bytes:
                self._mac_item.set_image_png(png_bytes, template=True)
            self._mac_item.set_title("")
            self._mac_item.set_tooltip("Tomato Clock")
        else:
            self._tray = QSystemTrayIcon()
            self._tray.setIcon(self._tray_base_icon)

        self._popup = TrayPopup()
        self._popup.on_toggle = self._engine.toggle
        self._popup.on_open_main = self._open_main_from_popup
        self._popup.on_quit = self.quit
        self._popup.hide()
        if self._tray is not None:
            self._tray.activated.connect(self._on_tray_activated)

        self._engine.state_changed.connect(self._on_state_changed)
        self._engine.phase_finished.connect(self._on_phase_finished)
        self._on_state_changed(self._engine.state())

        if self._tray is not None:
            self._tray.show()
        QTimer.singleShot(0, self._main_window.show_focus)
        QTimer.singleShot(350, self._mark_popup_ready)

    def show_popup(self) -> None:
        if not self._popup_ready:
            return
        if self._popup.isVisible() and not self._popup.is_hiding():
            self._popup.hide_animated()
            return
        self._show_popup_near_tray_icon()

    def _show_popup_near_tray_icon(self) -> None:
        if self._use_macos_status_item or self._tray is None:
            cursor = QCursor.pos()
            screen = QGuiApplication.screenAt(cursor) or QApplication.primaryScreen()
            if screen is None:
                self._popup.show_at(QPoint(cursor.x(), cursor.y()))
            else:
                geo = screen.availableGeometry()
                x = cursor.x() - int(self._popup.width() / 2)
                x = max(geo.x(), min(x, geo.x() + geo.width() - self._popup.width()))
                y = cursor.y() + 8
                if y + self._popup.height() > geo.y() + geo.height():
                    y = max(geo.y(), cursor.y() - self._popup.height() - 8)
                self._popup.show_at(QPoint(x, y))
            return

        tray_geo = self._tray.geometry()
        if tray_geo.width() <= 0 or tray_geo.height() <= 0:
            cursor = QCursor.pos()
            screen = QGuiApplication.screenAt(cursor) or QApplication.primaryScreen()
            if screen is None:
                self._popup.show_at(QPoint(cursor.x(), cursor.y()))
            else:
                geo = screen.availableGeometry()
                x = cursor.x() - int(self._popup.width() / 2)
                x = max(geo.x(), min(x, geo.x() + geo.width() - self._popup.width()))
                y = cursor.y() + 8
                if y + self._popup.height() > geo.y() + geo.height():
                    y = max(geo.y(), cursor.y() - self._popup.height() - 8)
                self._popup.show_at(QPoint(x, y))
            return

        screen = QGuiApplication.screenAt(tray_geo.center()) or QApplication.primaryScreen()
        if screen is None:
            x = tray_geo.x()
            y = tray_geo.y() + tray_geo.height()
            self._popup.show_at(QPoint(x, y))
            return

        geo = screen.availableGeometry()
        x = tray_geo.center().x() - int(self._popup.width() / 2)
        x = max(geo.x(), min(x, geo.x() + geo.width() - self._popup.width()))
        y = tray_geo.y() + tray_geo.height() + 8
        if y + self._popup.height() > geo.y() + geo.height():
            y = max(geo.y(), tray_geo.y() - self._popup.height() - 8)

        self._popup.show_at(QPoint(x, y))

    def _open_main_from_popup(self) -> None:
        self._popup.hide_animated()
        self._main_window.show_focus()

    def _mark_popup_ready(self) -> None:
        self._popup_ready = True

    def _on_tray_activated(self, reason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.Context,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_popup()

    def _on_state_changed(self, state: EngineState) -> None:
        if state.focus_type != self._last_focus_type:
            self._last_focus_type = state.focus_type
            self._focus_type_colors = self._settings.focus_type_colors()
        focus_color = self._focus_type_colors.get(state.focus_type, "#4F46E5")
        self._popup.set_time_text(state.time_str)
        self._popup.set_focus_type_text(state.focus_type, color_hex=focus_color)
        self._popup.set_running(state.running)

        if self._use_macos_status_item and self._mac_item is not None:
            self._mac_item.set_tooltip(f"Tomato Clock · {state.time_str}")
            if state.running:
                self._mac_item.set_title(f" {state.time_str}")
            else:
                self._mac_item.set_title("")
            return

        if self._tray is not None:
            self._tray.setToolTip(f"Tomato Clock · {state.time_str}")
            if state.running:
                if sys.platform == "win32":
                    self._tray.setIcon(self._tray_base_icon)
                else:
                    self._tray.setIcon(self._build_tray_icon_with_time(state.time_str))
            else:
                self._tray.setIcon(self._tray_base_icon)

    def _on_phase_finished(self, event: PhaseFinishedEvent) -> None:
        QApplication.beep()
        QTimer.singleShot(180, QApplication.beep)
        self._show_system_notification("番茄专注", event.prompt_message)

    def _show_system_notification(self, title: str, message: str) -> None:
        title = str(title)
        message = str(message)
        if sys.platform == "darwin" and self._mac_notification is not None:
            self._mac_notification.show_message(title, message)
            return

        if sys.platform == "win32" and show_windows_notification(title, message):
            return

        if self._tray is not None and QSystemTrayIcon.supportsMessages():
            if sys.platform == "win32":
                self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 4500)
            else:
                self._tray.showMessage(title, message, self._app_icon, 4500)
            return

        show_linux_notification(title, message)

    def _make_tray_color_icon(self, icon: QIcon) -> QIcon:
        size = 18
        screen = QApplication.primaryScreen()
        dpr = float(screen.devicePixelRatio()) if screen is not None else 2.0
        source = icon.pixmap(int(size * dpr), int(size * dpr))
        source.setDevicePixelRatio(dpr)

        source = self._remove_solid_background(source, tolerance=80)
        return QIcon(source)

    def _icon_to_png_bytes(self, icon: QIcon, size: int, dpr_override: float | None = None) -> bytes:
        if dpr_override is not None:
            dpr = float(dpr_override)
        else:
            screen = QApplication.primaryScreen()
            dpr = float(screen.devicePixelRatio()) if screen is not None else 2.0
        pixmap = icon.pixmap(int(size * dpr), int(size * dpr))
        pixmap.setDevicePixelRatio(dpr)
        pixmap = self._remove_solid_background(pixmap, tolerance=80)

        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        pixmap.toImage().save(buffer, "PNG")
        buffer.close()
        return data.data()

    def _remove_solid_background(self, pixmap: QPixmap, tolerance: int) -> QPixmap:
        image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        w = image.width()
        h = image.height()
        if w <= 0 or h <= 0:
            return pixmap

        corners = [
            image.pixelColor(0, 0),
            image.pixelColor(w - 1, 0),
            image.pixelColor(0, h - 1),
            image.pixelColor(w - 1, h - 1),
        ]

        for y in range(h):
            for x in range(w):
                c = image.pixelColor(x, y)
                if c.alpha() == 0:
                    continue
                for bg in corners:
                    if (
                        abs(c.red() - bg.red()) <= tolerance
                        and abs(c.green() - bg.green()) <= tolerance
                        and abs(c.blue() - bg.blue()) <= tolerance
                    ):
                        c.setAlpha(0)
                        image.setPixelColor(x, y, c)
                        break

        out = QPixmap.fromImage(image)
        out.setDevicePixelRatio(pixmap.devicePixelRatio())
        return out

    def _build_tray_icon_with_time(self, time_str: str) -> QIcon:
        height = 18
        padding = 8
        icon_size = 16

        screen = QApplication.primaryScreen()
        dpr = float(screen.devicePixelRatio()) if screen is not None else 2.0

        font = QFont("Menlo", 16, QFont.Weight.Bold)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(time_str)

        width = height + padding + text_width + padding
        pixmap = QPixmap(int(width * dpr), int(height * dpr))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        painter.setPen(QApplication.palette().color(QPalette.ColorRole.WindowText))
        painter.setFont(font)

        base_pixmap = self._tray_base_icon.pixmap(int(icon_size * dpr), int(icon_size * dpr))
        base_pixmap.setDevicePixelRatio(dpr)
        painter.drawPixmap(int((height - icon_size) / 2), int((height - icon_size) / 2), base_pixmap)
        painter.drawText(
            height + padding,
            0,
            width - (height + padding),
            height,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            time_str,
        )
        painter.end()

        return QIcon(pixmap)

    def quit(self) -> None:
        if self._tray is not None:
            self._tray.hide()
        if self._mac_item is not None:
            self._mac_item.remove()
        self._popup.close()
        self._main_window.close()
        QApplication.quit()
