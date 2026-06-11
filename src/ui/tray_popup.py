from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
)
from PyQt6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QRegion
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStyle, QVBoxLayout, QWidget

from src.ui.ui_theme import ACCENT, BG, BORDER, TEXT, apply_fixed_policy, rgba, type_colors


class TrayPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.on_toggle: Callable[[], None] | None = None
        self.on_open_main: Callable[[], None] | None = None
        self.on_quit: Callable[[], None] | None = None
        self.setObjectName("TrayPopupRoot")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setFixedSize(320, 156)
        self._accent = QColor()
        self._accent.setNamedColor("#4F46E5")
        self._bg0 = QColor(BG)
        self._bg1 = QColor("#FFF8F3")
        self._corner_radius = 18
        self._anim: QPropertyAnimation | None = None
        self._hiding = False
        self._update_mask()

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        self.time_label = QLabel("25:00", self)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        apply_fixed_policy(self.time_label, 48)
        self.time_label.setStyleSheet(f"font-size: 44px; font-weight: 700; color: {TEXT};")

        self.type_pill = QLabel("默认专注", self)
        self.type_pill.setObjectName("FocusTypePill")
        self.type_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        apply_fixed_policy(self.type_pill, 28)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)

        self.toggle_button = QPushButton("开始", self)
        self.toggle_button.setObjectName("ActionButton")
        apply_fixed_policy(self.toggle_button, 36)
        self.toggle_button.clicked.connect(self._handle_toggle)

        self.open_main_button = QPushButton("", self)
        self.open_main_button.setObjectName("ActionButton")
        apply_fixed_policy(self.open_main_button, 36)
        self.open_main_button.setFixedWidth(36)
        self.open_main_button.setToolTip("主窗口")
        self.open_main_button.clicked.connect(self._handle_open_main)

        self.quit_button = QPushButton("", self)
        self.quit_button.setObjectName("ActionButton")
        apply_fixed_policy(self.quit_button, 36)
        self.quit_button.setFixedWidth(36)
        self.quit_button.setToolTip("退出")
        self.quit_button.clicked.connect(self._handle_quit)

        self.toggle_button.setIcon(self._icon_for_toggle(running=False))
        self.open_main_button.setIcon(self._standard_icon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.quit_button.setIcon(self._standard_icon(QStyle.StandardPixmap.SP_DialogCloseButton))
        for btn in (self.toggle_button, self.open_main_button, self.quit_button):
            btn.setIconSize(QSize(16, 16))

        actions_row.addWidget(self.toggle_button, 1)
        actions_row.addWidget(self.open_main_button, 1)
        actions_row.addWidget(self.quit_button, 1)

        root.addWidget(self.time_label)
        root.addWidget(self.type_pill)
        root.addLayout(actions_row)
        root.addStretch(1)
        self._apply_theme()

    def set_time_text(self, text: str) -> None:
        self.time_label.setText(text)

    def set_focus_type_text(self, text: str, *, color_hex: str | None = None) -> None:
        self.type_pill.setText(str(text))
        if isinstance(color_hex, str) and color_hex.startswith("#"):
            c = QColor()
            c.setNamedColor(color_hex)
            if c.isValid():
                self._accent = QColor(c)
                self._apply_theme()

    def set_running(self, running: bool) -> None:
        self.toggle_button.setText("暂停" if running else "开始")
        self.toggle_button.setIcon(self._icon_for_toggle(running=running))

    def focusOutEvent(self, event):
        self.hide_animated()
        super().focusOutEvent(event)

    def resizeEvent(self, event) -> None:
        self._update_mask()
        super().resizeEvent(event)

    def show_at(self, pos: QPoint) -> None:
        self._hiding = False
        self._stop_anim()
        end_pos = QPoint(int(pos.x()), int(pos.y()))
        start_pos = QPoint(end_pos.x(), end_pos.y() + 10)
        self.move(start_pos)
        self.show()
        self.raise_()
        self.activateWindow()

        anim = QPropertyAnimation(self, b"pos", self)
        anim.setStartValue(start_pos)
        anim.setEndValue(end_pos)
        anim.setDuration(200)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(self._clear_anim)
        self._anim = anim
        anim.start()

    def hide_animated(self) -> None:
        if not self.isVisible() or self._hiding:
            return
        self._hiding = True
        self._stop_anim()
        start_pos = self.pos()
        end_pos = QPoint(start_pos.x(), start_pos.y() + 10)

        anim = QPropertyAnimation(self, b"pos", self)
        anim.setStartValue(start_pos)
        anim.setEndValue(end_pos)
        anim.setDuration(160)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self._finish_hide)
        self._anim = anim
        anim.start()

    def _finish_hide(self) -> None:
        if not self._hiding:
            return
        self._hiding = False
        self.hide()

    def is_hiding(self) -> bool:
        return bool(self._hiding)

    def _apply_theme(self) -> None:
        r = int(self._accent.red())
        g = int(self._accent.green())
        b = int(self._accent.blue())
        accent_hex = self._accent.name()
        btn_bg = accent_hex
        btn_bg_hover = QColor(accent_hex).darker(108).name()
        pill_bg_hex, pill_bd_hex, pill_text = type_colors(accent_hex)
        self._bg1 = QColor.fromRgb(
            int(round(255 - (255 - r) * 0.10)),
            int(round(255 - (255 - g) * 0.10)),
            int(round(255 - (255 - b) * 0.10)),
        )
        self.setStyleSheet(
            "QWidget#TrayPopupRoot { background: transparent; }"
            f"QLabel {{ color: {TEXT}; }}"
            "#FocusTypePill {"
            f"  background-color: {pill_bg_hex};"
            f"  border: 1px solid {pill_bd_hex};"
            "  border-radius: 999px;"
            "  padding: 4px 12px;"
            f"  color: {pill_text};"
            "  font-size: 13px;"
            "  font-weight: 600;"
            "}"
            "QPushButton#ActionButton {"
            f"  background-color: {btn_bg};"
            "  color: white;"
            f"  border: 1px solid {btn_bg};"
            "  border-radius: 8px;"
            "  padding: 7px 10px;"
            "  font-size: 13px;"
            "  font-weight: 600;"
            "}"
            f"QPushButton#ActionButton:hover {{ background-color: {btn_bg_hover}; }}"
            "QPushButton#ActionButton:pressed { background-color: #C1272D; }"
        )
        if hasattr(self, "open_main_button"):
            self.open_main_button.setStyleSheet(
                f"QPushButton#ActionButton {{ background: white; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 0; }}"
                f"QPushButton#ActionButton:hover {{ background: {rgba(ACCENT, 0.08)}; color: {ACCENT}; }}"
            )
        if hasattr(self, "quit_button"):
            self.quit_button.setStyleSheet(
                f"QPushButton#ActionButton {{ background: white; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 0; }}"
                f"QPushButton#ActionButton:hover {{ background: {rgba(ACCENT, 0.08)}; color: {ACCENT}; }}"
            )
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect().adjusted(1, 1, -1, -1)
        grad = QLinearGradient(QPointF(rect.topLeft()), QPointF(rect.bottomRight()))
        grad.setColorAt(0.0, self._bg0)
        grad.setColorAt(1.0, self._bg1)
        painter.setPen(QPen(QColor.fromRgb(209, 213, 219), 1))
        painter.setBrush(grad)
        painter.drawRoundedRect(rect, self._corner_radius, self._corner_radius)
        painter.fillRect(int(rect.x()), int(rect.y()), int(rect.width()), 3, self._accent)
        painter.end()

    def _update_mask(self) -> None:
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), float(self._corner_radius), float(self._corner_radius))
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def _stop_anim(self) -> None:
        if self._anim is not None:
            self._anim.stop()
            self._anim.deleteLater()
            self._anim = None

    def _clear_anim(self) -> None:
        sender = self.sender()
        if isinstance(sender, QPropertyAnimation):
            sender.deleteLater()
            if self._anim is sender:
                self._anim = None
        else:
            self._anim = None

    def _standard_icon(self, pixmap: QStyle.StandardPixmap) -> QIcon:
        style = self.style()
        if style is None:
            return QIcon()
        return style.standardIcon(pixmap)

    def _icon_for_toggle(self, *, running: bool) -> QIcon:
        if running:
            return self._standard_icon(QStyle.StandardPixmap.SP_MediaPause)
        return self._standard_icon(QStyle.StandardPixmap.SP_MediaPlay)

    def _handle_toggle(self) -> None:
        if callable(self.on_toggle):
            self.on_toggle()

    def _handle_open_main(self) -> None:
        if callable(self.on_open_main):
            self.on_open_main()

    def _handle_quit(self) -> None:
        if callable(self.on_quit):
            self.on_quit()
