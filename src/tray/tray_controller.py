from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QCursor, QFont, QFontMetrics, QGuiApplication, QIcon, QImage, QPainter, QPalette, QPixmap
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from src.core.pomodoro_engine import EngineState, PomodoroEngine
from src.ui.main_window import MainWindow
from src.ui.tray_popup import TrayPopup


class TrayController:
    def __init__(self, engine: PomodoroEngine, main_window: MainWindow, app_icon: QIcon):
        self._engine = engine
        self._main_window = main_window
        self._app_icon = app_icon
        self._tray_base_icon = self._make_tray_color_icon(self._app_icon)

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

    def show_popup(self) -> None:
        self._show_popup_near_tray_icon()

    def _show_popup_near_tray_icon(self) -> None:
        tray_geo = self._tray.geometry()
        if tray_geo.width() <= 0 or tray_geo.height() <= 0:
            cursor = QCursor.pos()
            screen = QGuiApplication.screenAt(cursor) or QApplication.primaryScreen()
            if screen is None:
                self._popup.move(cursor.x(), cursor.y())
            else:
                geo = screen.availableGeometry()
                x = cursor.x() - int(self._popup.width() / 2)
                x = max(geo.x(), min(x, geo.x() + geo.width() - self._popup.width()))
                y = cursor.y() + 8
                if y + self._popup.height() > geo.y() + geo.height():
                    y = max(geo.y(), cursor.y() - self._popup.height() - 8)
                self._popup.move(x, y)
            self._popup.show()
            self._popup.raise_()
            self._popup.activateWindow()
            return

        screen = QGuiApplication.screenAt(tray_geo.center()) or QApplication.primaryScreen()
        if screen is None:
            x = tray_geo.x()
            y = tray_geo.y() + tray_geo.height()
            self._popup.move(x, y)
            self._popup.show()
            self._popup.raise_()
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
        self._popup.raise_()
        self._popup.activateWindow()

    def _on_tray_activated(self, reason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.Context,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_popup()

    def _on_state_changed(self, state: EngineState) -> None:
        self._popup.set_time_text(state.time_str)
        self._popup.set_focus_type_text(state.focus_type)
        self._popup.set_running(state.running)

        self._tray.setToolTip(f"Tomato Clock · {state.time_str}")
        if state.running:
            self._tray.setIcon(self._build_tray_icon_with_time(state.time_str))
        else:
            self._tray.setIcon(self._tray_base_icon)

    def _make_tray_color_icon(self, icon: QIcon) -> QIcon:
        size = 18
        screen = QApplication.primaryScreen()
        dpr = float(screen.devicePixelRatio()) if screen is not None else 2.0
        source = icon.pixmap(int(size * dpr), int(size * dpr))
        source.setDevicePixelRatio(dpr)

        source = self._remove_solid_background(source, tolerance=80)
        return QIcon(source)

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
        self._tray.hide()
        self._popup.close()
        self._main_window.close()
        QApplication.quit()
