from __future__ import annotations

from PyQt6.QtCore import QByteArray, Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy, QWidget


class BottomNavBar(QWidget):
    current_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: list[QPushButton] = []
        self._current = 0

        self.setFixedHeight(78)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            "BottomNavBar { background: rgba(255,255,255,0.92); border-top: 1px solid rgba(0,0,0,0.10); }"
            "QPushButton { border: 0; margin: 0; background: transparent; color: rgba(0,0,0,0.62); font-size: 16px; font-weight: 650; padding: 0 16px; }"
            "QPushButton:hover { background: rgba(0,0,0,0.06); }"
            "QPushButton#nav_focus:checked { background: rgba(79,70,229,0.14); color: #4F46E5; }"
            "QPushButton#nav_stats:checked { background: rgba(16,185,129,0.14); color: #10B981; }"
            "QPushButton#nav_settings:checked { background: rgba(249,115,22,0.14); color: #F97316; }"
            "QPushButton#nav_focus:hover { background: rgba(79,70,229,0.10); }"
            "QPushButton#nav_stats:hover { background: rgba(16,185,129,0.10); }"
            "QPushButton#nav_settings:hover { background: rgba(249,115,22,0.10); }"
        )

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def set_items(self, labels: list[str]) -> None:
        for b in self._buttons:
            self._layout.removeWidget(b)
            b.deleteLater()
        self._buttons = []

        accent_map = {
            "专注": QColor("#4F46E5"),
            "统计": QColor("#10B981"),
            "设置": QColor("#F97316"),
        }
        icon_map = {
            "专注": self._make_tab_icon(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2"/></svg>'
            ),
            "统计": self._make_tab_icon(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19V5"/><path d="M4 19h16"/><path d="M8 16v-6"/><path d="M12 16v-9"/><path d="M16 16v-4"/></svg>'
            ),
            "设置": self._make_tab_icon(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09A1.65 1.65 0 0 0 15 4.6a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.06.17.1.35.1.54s-.04.37-.1.54A1.65 1.65 0 0 0 20.91 11H21a2 2 0 1 1 0 4h-.09A1.65 1.65 0 0 0 19.4 15Z"/></svg>'
            ),
        }

        for idx, label in enumerate(labels):
            btn = QPushButton(label, self)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            if label == "专注":
                btn.setObjectName("nav_focus")
            elif label == "统计":
                btn.setObjectName("nav_stats")
            elif label == "设置":
                btn.setObjectName("nav_settings")

            icon = icon_map.get(label)
            accent = accent_map.get(label, QColor("#111827"))
            if icon is not None:
                btn.setIcon(self._recolor_icon(icon, accent=accent))
                btn.setIconSize(QSize(22, 22))
            btn.clicked.connect(lambda _checked=False, i=idx: self.set_current_index(i))
            self._layout.addWidget(btn, 1)
            self._buttons.append(btn)

        self.set_current_index(0)

    def set_current_index(self, index: int) -> None:
        if index < 0 or index >= len(self._buttons):
            return
        self._current = index
        for i, b in enumerate(self._buttons):
            b.setChecked(i == index)
        self.current_changed.emit(index)

    def _make_tab_icon(self, svg: str) -> QIcon:
        normal = self._render_svg(svg, 22, QColor("#6B7280"))
        selected = self._render_svg(svg, 22, QColor("#111827"))
        icon = QIcon()
        icon.addPixmap(normal, QIcon.Mode.Normal, QIcon.State.Off)
        icon.addPixmap(selected, QIcon.Mode.Normal, QIcon.State.On)
        return icon

    def _recolor_icon(self, base: QIcon, accent: QColor) -> QIcon:
        off = base.pixmap(22, 22, QIcon.Mode.Normal, QIcon.State.Off)
        on = self._tint_pixmap(off, accent)
        icon = QIcon()
        icon.addPixmap(off, QIcon.Mode.Normal, QIcon.State.Off)
        icon.addPixmap(on, QIcon.Mode.Normal, QIcon.State.On)
        return icon

    def _tint_pixmap(self, pixmap: QPixmap, color: QColor) -> QPixmap:
        out = QPixmap(pixmap.size())
        out.fill(Qt.GlobalColor.transparent)
        painter = QPainter(out)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(out.rect(), color)
        painter.end()
        return out

    def _render_svg(self, svg: str, size: int, color: QColor) -> QPixmap:
        svg = svg.replace("currentColor", color.name())
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        renderer.render(painter)
        painter.end()
        return pixmap
