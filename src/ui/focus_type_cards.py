from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget


def make_icon(kind: str, color: QColor) -> QIcon:
    size = 18
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    pen = QPen(color)
    pen.setWidth(2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if kind == "plus":
        painter.drawLine(int(size / 2), 4, int(size / 2), size - 4)
        painter.drawLine(4, int(size / 2), size - 4, int(size / 2))
    elif kind == "trash":
        painter.drawRect(6, 7, 6, 8)
        painter.drawLine(5, 7, 13, 7)
        painter.drawLine(7, 5, 11, 5)
        painter.drawLine(8, 4, 10, 4)
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
        is_new: bool = False,
    ):
        super().__init__()
        self._focus_type = focus_type
        self._color_hex = color_hex
        self._on_select = on_select
        self._on_delete = on_delete
        self._on_color = on_color
        self._is_new = is_new

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(104)

        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        self.label = QLabel(self._focus_type, self)
        self.label.setStyleSheet("font-size: 17px; font-weight: 750;")
        root.addWidget(self.label, 1)

        self.color_btn = QToolButton(self)
        self.color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.color_btn.setIcon(make_icon("palette", QColor("#111827")))
        self.color_btn.setIconSize(QPixmap(18, 18).size())
        self.color_btn.clicked.connect(self._handle_color)

        self.delete_btn = QToolButton(self)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setIcon(make_icon("trash", QColor("#111827")))
        self.delete_btn.setIconSize(QPixmap(18, 18).size())
        self.delete_btn.clicked.connect(self._handle_delete)
        self.delete_btn.hide()

        self.add_btn = QToolButton(self)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setIcon(make_icon("plus", QColor("#111827")))
        self.add_btn.setIconSize(QPixmap(18, 18).size())
        self.add_btn.hide()

        for b in (self.color_btn, self.delete_btn, self.add_btn):
            b.setStyleSheet("QToolButton { background: transparent; border: 0; padding: 6px; }")

        if self._is_new:
            self.label.setText("新建")
            self.add_btn.show()
            root.addWidget(self.add_btn, 0)
        else:
            root.addWidget(self.color_btn, 0)
            if self._on_delete is not None:
                root.addWidget(self.delete_btn, 0)

        self._apply_style(hover=False)

    def enterEvent(self, event):
        if not self._is_new and self._on_delete is not None:
            self.delete_btn.show()
        self._apply_style(hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._is_new and self._on_delete is not None:
            self.delete_btn.hide()
        self._apply_style(hover=False)
        super().leaveEvent(event)

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
        bg_color = base.lighter(175)
        border_color = base
        bg = f"rgba({bg_color.red()},{bg_color.green()},{bg_color.blue()},1.0)"
        border = (
            f"rgba({border_color.red()},{border_color.green()},{border_color.blue()},0.62)"
            if hover
            else f"rgba({border_color.red()},{border_color.green()},{border_color.blue()},0.40)"
        )
        self.setStyleSheet(
            "QWidget {"
            f"background: {bg};"
            f"border: 1px solid {border};"
            "border-radius: 18px;"
            "}"
        )

    def _handle_delete(self) -> None:
        if self._on_delete is not None:
            self._on_delete(self._focus_type)

    def _handle_color(self) -> None:
        if self._on_color is not None:
            self._on_color(self._focus_type)

