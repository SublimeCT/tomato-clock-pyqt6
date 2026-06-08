from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QCursor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget


def make_icon(kind: str, color: QColor, size: int = 22) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    pen = QPen(color)
    pen.setWidth(max(2, int(round(size / 11))))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    def u(v: float) -> int:
        return int(round(v * size))

    if kind == "plus":
        painter.drawLine(u(0.50), u(0.18), u(0.50), u(0.82))
        painter.drawLine(u(0.18), u(0.50), u(0.82), u(0.50))
    elif kind == "trash":
        left, right = u(0.30), u(0.70)
        top, bottom = u(0.34), u(0.78)
        lid_y = u(0.28)
        handle_top = u(0.20)
        handle_w = u(0.14)
        cx = u(0.50)

        painter.drawRoundedRect(left, top, right - left, bottom - top, u(0.06), u(0.06))
        painter.drawLine(u(0.24), top, u(0.76), top)
        painter.drawLine(u(0.26), lid_y, u(0.74), lid_y)
        painter.drawLine(cx - handle_w // 2, handle_top, cx + handle_w // 2, handle_top)
    elif kind == "edit":
        x1, y1 = u(0.22), u(0.78)
        x2, y2 = u(0.76), u(0.24)
        painter.drawLine(x1, y1, x2, y2)
        painter.drawLine(u(0.70), u(0.18), u(0.82), u(0.30))
        painter.drawLine(u(0.76), u(0.24), u(0.80), u(0.28))
    elif kind == "palette":
        painter.drawEllipse(u(0.18), u(0.18), u(0.64), u(0.64))
        dot = max(2, u(0.06))
        painter.drawEllipse(u(0.62), u(0.44), dot, dot)
        painter.drawEllipse(u(0.46), u(0.62), dot, dot)
    else:
        painter.drawEllipse(4, 4, 10, 10)
        painter.drawEllipse(8, 6, 2, 2)
        painter.drawEllipse(6, 9, 2, 2)
        painter.drawEllipse(10, 10, 2, 2)

    painter.end()
    return QIcon(pixmap)


class FocusTypeCard(QWidget):
    def __init__(
        self,
        focus_type: str,
        color_hex: str,
        on_select: Callable[[str], None],
        on_delete: Callable[[str], None] | None,
        on_color: Callable[[str], None] | None,
        on_edit: Callable[[str], None] | None = None,
        selected: bool = False,
        locked: bool = False,
    ):
        super().__init__()
        self._focus_type = focus_type
        self._color_hex = color_hex
        self._on_select = on_select
        self._on_delete = on_delete
        self._on_color = on_color
        self._on_edit = on_edit
        self._selected = bool(selected)
        self._locked = bool(locked)
        self._hover = False
        self._bg = QColor(255, 255, 255, 0)
        self._border = QColor(0, 0, 0, 0)
        self._border_w = 1

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("FocusTypeCard")
        self.setFixedHeight(104)
        self.setFixedWidth(290)
        self.setMouseTracking(True)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(18)
        self._shadow.setOffset(0, 8)
        self._shadow.setColor(QColor(0, 0, 0, 25))
        self.setGraphicsEffect(self._shadow)

        root = QHBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(6)

        base = QColor(self._color_hex) if QColor(self._color_hex).isValid() else QColor("#4F46E5")
        if not self._locked:
            avatar = QLabel(self)
            avatar.setFixedSize(28, 28)
            avatar_pm = QPixmap(28, 28)
            avatar_pm.fill(Qt.GlobalColor.transparent)
            p = QPainter(avatar_pm)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(base.red(), base.green(), base.blue(), 210))
            p.drawEllipse(0, 0, 28, 28)
            p.setBrush(QColor(255, 255, 255, 220))
            p.drawEllipse(10, 10, 8, 8)
            p.end()
            avatar.setPixmap(avatar_pm)
            root.addWidget(avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        self.label = QLabel(self._focus_type, self)
        self.label.setStyleSheet("font-size: 18px; font-weight: 750; background: transparent; color: rgba(0,0,0,0.86);")
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        root.addWidget(self.label, 1)

        if not self._locked:
            icon_color = base.darker(130)
            btn_bg = f"rgba({base.red()},{base.green()},{base.blue()},0.14)"
            btn_bg_hover = f"rgba({base.red()},{base.green()},{base.blue()},0.20)"

            def build_btn(icon_kind: str) -> QToolButton:
                b = QToolButton(self)
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.setIcon(make_icon(icon_kind, icon_color, size=32))
                b.setIconSize(QSize(28, 28))
                b.setFixedSize(48, 48)
                b.setStyleSheet(
                    "QToolButton { border: 0; padding: 10px; border-radius: 18px; background: transparent; }"
                    f"QToolButton:hover {{ background: {btn_bg}; }}"
                    f"QToolButton:pressed {{ background: {btn_bg_hover}; }}"
                )
                return b

            if self._on_color is not None:
                self.color_btn = build_btn("palette")
                self.color_btn.clicked.connect(self._handle_color)
                root.addWidget(self.color_btn, 0, Qt.AlignmentFlag.AlignVCenter)

            if self._on_edit is not None:
                self.edit_btn = build_btn("edit")
                self.edit_btn.clicked.connect(self._handle_edit)
                root.addWidget(self.edit_btn, 0, Qt.AlignmentFlag.AlignVCenter)

            if self._on_delete is not None:
                self.delete_btn = build_btn("trash")
                self.delete_btn.clicked.connect(self._handle_delete)
                root.addWidget(self.delete_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self._apply_style(hover=False)

    def enterEvent(self, event):
        self._hover = True
        self._apply_style(hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._apply_style(hover=False)
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(self._border, self._border_w))
        painter.setBrush(self._bg)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 18, 18)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            if isinstance(child, QToolButton):
                super().mousePressEvent(event)
                return
            self._on_select(self._focus_type)
        super().mousePressEvent(event)

    def _apply_style(self, hover: bool) -> None:
        base = QColor(self._color_hex) if QColor(self._color_hex).isValid() else QColor("#4F46E5")
        r, g, b = base.red(), base.green(), base.blue()
        if self._selected:
            bg_a = 0.20
            border_a = 0.70
            border_w = 2
            shadow_alpha = 38
            shadow_blur = 26
            shadow_offset = 12
            text_alpha = 0.92
        elif hover:
            bg_a = 0.14
            border_a = 0.38
            border_w = 1
            shadow_alpha = 26
            shadow_blur = 22
            shadow_offset = 10
            text_alpha = 0.88
        else:
            bg_a = 0.10
            border_a = 0.22
            border_w = 1
            shadow_alpha = 14
            shadow_blur = 18
            shadow_offset = 8
            text_alpha = 0.86

        self._bg = QColor(r, g, b, int(bg_a * 255))
        self._border = QColor(r, g, b, int(border_a * 255))
        self._border_w = int(border_w)
        self.label.setStyleSheet(
            f"font-size: 18px; font-weight: 750; background: transparent; color: rgba(0,0,0,{text_alpha:.2f});"
        )
        self._shadow.setColor(QColor(0, 0, 0, shadow_alpha))
        self._shadow.setBlurRadius(shadow_blur)
        self._shadow.setOffset(0, shadow_offset)
        self.update()

    def _handle_delete(self) -> None:
        if self._on_delete is not None:
            self._on_delete(self._focus_type)

    def _handle_color(self) -> None:
        if self._on_color is not None:
            self._on_color(self._focus_type)

    def _handle_edit(self) -> None:
        if self._on_edit is not None:
            self._on_edit(self._focus_type)

    def set_selected(self, selected: bool) -> None:
        self._selected = bool(selected)
        self._apply_style(hover=self._hover)
