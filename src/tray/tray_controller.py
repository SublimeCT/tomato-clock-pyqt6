from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QFontMetrics, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from src.core.pomodoro_engine import EngineState, PomodoroEngine
from src.ui.main_window import MainWindow
from src.ui.tray_popup import TrayPopup


class TrayController:
    def __init__(self, engine: PomodoroEngine, main_window: MainWindow, app_icon: QIcon):
        self._engine = engine
        self._main_window = main_window
        self._app_icon = app_icon
        self._tray_base_icon = self._make_template_icon(self._app_icon)

        self._tray = QSystemTrayIcon()
        self._tray.setIcon(self._tray_base_icon)

        self._popup = TrayPopup()
        self._popup.on_toggle = self._engine.toggle
        self._popup.on_open_main = self._main_window.show_focus
        self._popup.on_quit = self.quit
        self._tray.activated.connect(self._on_tray_activated)

        self._engine.state_changed.connect(self._on_state_changed)
        self._on_state_changed(self._engine.state())

        self._tray.show()
        QTimer.singleShot(0, self._main_window.show_focus)

    def toggle_popup(self) -> None:
        if self._popup.isVisible():
            self._popup.hide()
            return
        self._show_popup_near_tray_icon()

    def _show_popup_near_tray_icon(self) -> None:
        screen = QApplication.primaryScreen()
        tray_geo = self._tray.geometry()
        if screen is None:
            x = tray_geo.x()
            y = tray_geo.y() + tray_geo.height()
            self._popup.move(x, y)
            self._popup.show()
            self._popup.activateWindow()
            return

        geo = screen.availableGeometry()
        x = tray_geo.center().x() - int(self._popup.width() / 2)
        x = max(geo.x(), min(x, geo.x() + geo.width() - self._popup.width()))
        y = tray_geo.y() + tray_geo.height() + 8
        if y + self._popup.height() > geo.y() + geo.height():
            y = max(geo.y(), tray_geo.y() - self._popup.height() - 8)

        self._popup.move(x, y)
        self._popup.show()
        self._popup.activateWindow()

    def _on_tray_activated(self, reason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.Context,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.toggle_popup()

    def _on_state_changed(self, state: EngineState) -> None:
        self._popup.set_time_text(state.time_str)
        self._popup.set_focus_type_text(state.focus_type)
        self._popup.set_running(state.running)

        self._tray.setToolTip(f"Tomato Clock · {state.time_str}")
        if state.running:
            self._tray.setIcon(self._build_tray_icon_with_time(state.time_str))
        else:
            self._tray.setIcon(self._tray_base_icon)

    def _make_template_icon(self, icon: QIcon) -> QIcon:
        size = 18
        screen = QApplication.primaryScreen()
        dpr = float(screen.devicePixelRatio()) if screen is not None else 2.0
        source = icon.pixmap(int(size * dpr), int(size * dpr))
        source.setDevicePixelRatio(dpr)

        out = QPixmap(source.size())
        out.setDevicePixelRatio(source.devicePixelRatio())
        out.fill(Qt.GlobalColor.transparent)

        painter = QPainter(out)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.fillRect(out.rect(), Qt.GlobalColor.black)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        painter.drawPixmap(0, 0, source)
        painter.end()

        template = QIcon(out)
        template.setIsMask(True)
        return template

    def _build_tray_icon_with_time(self, time_str: str) -> QIcon:
        height = 18
        padding = 8
        icon_size = 16

        screen = QApplication.primaryScreen()
        dpr = float(screen.devicePixelRatio()) if screen is not None else 2.0

        font = QFont("Menlo", 14, QFont.Weight.Bold)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(time_str)

        width = height + padding + text_width + padding
        pixmap = QPixmap(int(width * dpr), int(height * dpr))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        painter.setPen(Qt.GlobalColor.black)
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

        icon = QIcon(pixmap)
        icon.setIsMask(True)
        return icon

    def quit(self) -> None:
        self._tray.hide()
        self._popup.close()
        self._main_window.close()
        QApplication.quit()
