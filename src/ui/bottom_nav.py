from __future__ import annotations

from PyQt6.QtCore import QByteArray, Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy, QStyle, QStyleOptionButton, QWidget

from src.ui.ui_theme import ACCENT, MUTED, TEXT, apply_fixed_policy, rgba


class VerticalIconButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        style = self.style()
        if style is None:
            super().paintEvent(event)
            return

        style.drawControl(QStyle.ControlElement.CE_PushButtonBevel, opt, painter, self)

        content = opt.rect.adjusted(10, 6, -10, -6)
        icon_size = self.iconSize()
        spacing = 5

        state = QIcon.State.On if self.isChecked() else QIcon.State.Off
        mode = QIcon.Mode.Normal if self.isEnabled() else QIcon.Mode.Disabled
        pm = self.icon().pixmap(icon_size, mode, state) if not self.icon().isNull() else QPixmap()

        y = content.y()
        if not pm.isNull():
            ix = content.x() + int((content.width() - icon_size.width()) / 2)
            painter.drawPixmap(ix, y, icon_size.width(), icon_size.height(), pm)
            y += icon_size.height() + spacing

        font = self.font()
        font.setPointSize(12)
        font.setWeight(600)
        painter.setFont(font)
        painter.setPen(opt.palette.buttonText().color())
        painter.drawText(
            content.x(),
            y,
            content.width(),
            max(0, content.height() - (y - content.y())),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            self.text(),
        )
        painter.end()


class BottomNavBar(QWidget):
    current_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: list[QPushButton] = []
        self._current = 0

        apply_fixed_policy(self, 78)
        self.setStyleSheet(
            f"BottomNavBar {{ background: rgba(255,255,255,0.88); border-top: 1px solid {rgba('#000000', 0.06)}; }}"
            f"QPushButton {{ border: 0; margin: 0; background: transparent; color: {MUTED}; font-size: 12px; font-weight: 600; padding: 6px 20px; border-radius: 12px; }}"
            f"QPushButton:hover {{ background: {rgba(ACCENT, 0.08)}; color: {TEXT}; }}"
            f"QPushButton:checked {{ background: {rgba(ACCENT, 0.10)}; color: {ACCENT}; }}"
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
            "模板": QColor("#F59E0B"),
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
            "模板": self._make_tab_icon(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></svg>'
            ),
        }

        icon_size = 24
        for idx, label in enumerate(labels):
            btn = VerticalIconButton(label, self)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(66)
            if label == "专注":
                btn.setObjectName("nav_focus")
            elif label == "统计":
                btn.setObjectName("nav_stats")
            elif label == "模板":
                btn.setObjectName("nav_templates")
            elif label == "设置":
                btn.setObjectName("nav_settings")

            icon = icon_map.get(label)
            accent = accent_map.get(label, QColor("#111827"))
            if icon is not None:
                btn.setIcon(self._recolor_icon(icon, accent=accent))
                btn.setIconSize(QSize(icon_size, icon_size))

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
        normal = self._render_svg(svg, 24, QColor(MUTED))
        selected = self._render_svg(svg, 24, QColor(ACCENT))
        icon = QIcon()
        icon.addPixmap(normal, QIcon.Mode.Normal, QIcon.State.Off)
        icon.addPixmap(selected, QIcon.Mode.Normal, QIcon.State.On)
        return icon

    def _recolor_icon(self, base: QIcon, accent: QColor) -> QIcon:
        off = base.pixmap(24, 24, QIcon.Mode.Normal, QIcon.State.Off)
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
