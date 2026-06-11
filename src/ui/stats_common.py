from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from PyQt6.QtCore import QPoint, Qt, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QToolTip, QVBoxLayout, QWidget

from src.ui.ui_theme import ACCENT, BORDER, MUTED, SUCCESS, TEXT, apply_fixed_policy, rgba


class StatsModeBar(QWidget):
    mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        self._mode = "day"
        self.setObjectName("StatsModeBar")
        apply_fixed_policy(self, 52)
        self.setStyleSheet(
            "QWidget#StatsModeBar { background: white; border: 1px solid rgba(0,0,0,0.06); border-radius: 12px; }"
            f"QPushButton {{ border: 0; background: transparent; font-size: 14px; font-weight: 600; color: {MUTED}; border-radius: 8px; }}"
            f"QPushButton:hover {{ color: {TEXT}; }}"
            f"QPushButton:checked {{ background: {rgba(SUCCESS, 0.10)}; color: {SUCCESS}; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        for key, label in (("day", "日"), ("week", "周"), ("month", "月"), ("year", "年")):
            btn = QPushButton(label, self)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(40)
            btn.clicked.connect(lambda _checked=False, mode=key: self.set_mode(mode))
            layout.addWidget(btn, 1)
            self._buttons[key] = btn
        self.set_mode("day")

    def set_mode(self, mode: str) -> None:
        if mode not in self._buttons:
            return
        self._mode = mode
        for key, btn in self._buttons.items():
            btn.setChecked(key == mode)
        self.mode_changed.emit(mode)


@dataclass(frozen=True)
class BarPoint:
    label: str
    value: int
    hint: str
    accent: bool = False


class ColumnBarChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._points: list[BarPoint] = []
        self.setMouseTracking(True)
        self.setMinimumHeight(208)

    def set_points(self, points: list[BarPoint]) -> None:
        self._points = list(points)
        self.update()

    def mouseMoveEvent(self, event) -> None:
        point = self._hit_test(event.pos())
        if point is None:
            QToolTip.hideText()
            return
        QToolTip.showText(event.globalPosition().toPoint(), point.hint, self)

    def leaveEvent(self, event) -> None:
        QToolTip.hideText()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect().adjusted(0, 0, -1, -1)
        axis_w = 34
        bottom_h = 24
        chart_rect = QRect(rect.left() + axis_w, rect.top() + 8, rect.width() - axis_w - 4, rect.height() - bottom_h - 16)
        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return

        max_value = max(60, max((p.value for p in self._points), default=0))
        painter.setPen(QPen(QColor(BORDER), 1))
        for idx in range(5):
            y = chart_rect.top() + int(chart_rect.height() * idx / 4)
            painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)
            tick = max_value - int(max_value * idx / 4)
            painter.setPen(QColor(MUTED))
            painter.drawText(rect.left(), y - 7, axis_w - 6, 14, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "0" if idx == 4 else f"{tick}m")
            painter.setPen(QPen(QColor(BORDER), 1))

        if not self._points:
            painter.setPen(QColor(MUTED))
            painter.drawText(chart_rect, Qt.AlignmentFlag.AlignCenter, "暂无数据")
            return

        column_w = max(10, int(chart_rect.width() / max(1, len(self._points))))
        bar_w = min(28, max(8, column_w - 6))
        label_step = 1 if len(self._points) <= 16 else 2 if len(self._points) <= 24 else 3
        for index, point in enumerate(self._points):
            col_x = chart_rect.left() + index * column_w
            bar_h = 0 if max_value <= 0 else int(chart_rect.height() * point.value / max_value)
            bar_rect = QRect(col_x + int((column_w - bar_w) / 2), chart_rect.bottom() - bar_h + 1, bar_w, max(2, bar_h))
            color = QColor(ACCENT if point.accent else SUCCESS)
            color.setAlpha(255 if point.accent else 165)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(bar_rect, 4, 4)
            if point.value > 0:
                painter.setPen(QColor(ACCENT if point.accent else TEXT))
                painter.drawText(QRect(col_x, bar_rect.top() - 18, column_w, 14), Qt.AlignmentFlag.AlignCenter, f"{point.value}m")
            if index % label_step == 0 or index == len(self._points) - 1:
                painter.setPen(QColor(MUTED))
                painter.drawText(QRect(col_x, chart_rect.bottom() + 8, column_w, 14), Qt.AlignmentFlag.AlignCenter, point.label)

    def _hit_test(self, pos: QPoint) -> BarPoint | None:
        if not self._points:
            return None
        rect = self.rect().adjusted(0, 0, -1, -1)
        axis_w = 34
        bottom_h = 24
        chart_rect = QRect(rect.left() + axis_w, rect.top() + 8, rect.width() - axis_w - 4, rect.height() - bottom_h - 16)
        if not chart_rect.contains(pos):
            return None
        column_w = max(10, int(chart_rect.width() / max(1, len(self._points))))
        index = min(len(self._points) - 1, max(0, int((pos.x() - chart_rect.left()) / column_w)))
        return self._points[index]


class HeatmapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._year = date.today().year
        self._counts: dict[str, int] = {}
        self.setMouseTracking(True)
        self.setMinimumHeight(88)

    def set_data(self, year: int, counts: dict[str, int]) -> None:
        self._year = int(year)
        self._counts = dict(counts)
        self.update()

    def mouseMoveEvent(self, event) -> None:
        info = self._hit_test(event.pos())
        if info is None:
            QToolTip.hideText()
            return
        day_key, value = info
        QToolTip.showText(event.globalPosition().toPoint(), f"{day_key}\n次数: {value}", self)

    def leaveEvent(self, event) -> None:
        QToolTip.hideText()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        start = date(self._year, 1, 1)
        end = date(self._year, 12, 31)
        start = start - timedelta(days=start.weekday())
        cell, gap = self._grid_metrics()
        rows = 7
        total_w = 53 * cell + 52 * gap
        total_h = rows * cell + (rows - 1) * gap
        origin_x = max(0, int((self.width() - total_w) / 2))
        origin_y = max(0, int((self.height() - total_h) / 2))
        max_count = max(1, max(self._counts.values(), default=0))
        day = start
        while day <= end:
            key = day.isoformat()
            value = int(self._counts.get(key, 0))
            week = int((day - start).days / 7)
            row = day.weekday()
            x = origin_x + week * (cell + gap)
            y = origin_y + row * (cell + gap)
            level = 0 if value <= 0 else min(4, max(1, round((value / max_count) * 4)))
            colors = ["#ECE6DE", rgba(SUCCESS, 0.24), rgba(SUCCESS, 0.42), rgba(SUCCESS, 0.62), SUCCESS]
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(colors[level]))
            painter.drawRoundedRect(QRect(x, y, cell, cell), 2, 2)
            day += timedelta(days=1)

    def _hit_test(self, pos: QPoint) -> tuple[str, int] | None:
        start = date(self._year, 1, 1)
        end = date(self._year, 12, 31)
        start = start - timedelta(days=start.weekday())
        cell, gap = self._grid_metrics()
        rows = 7
        total_w = 53 * cell + 52 * gap
        total_h = rows * cell + (rows - 1) * gap
        origin_x = max(0, int((self.width() - total_w) / 2))
        origin_y = max(0, int((self.height() - total_h) / 2))
        day = start
        while day <= end:
            week = int((day - start).days / 7)
            row = day.weekday()
            rect = QRect(origin_x + week * (cell + gap), origin_y + row * (cell + gap), cell, cell)
            if rect.contains(pos):
                key = day.isoformat()
                return key, int(self._counts.get(key, 0))
            day += timedelta(days=1)
        return None

    def _grid_metrics(self) -> tuple[int, int]:
        columns = 53
        gap = 1
        available = max(240, self.width() - ((columns - 1) * gap))
        cell = max(3, min(7, int(available / columns)))
        return cell, gap


def make_card(title: str, value: str, color: str, parent: QWidget) -> tuple[QWidget, QLabel]:
    card = QWidget(parent)
    card.setObjectName("StatsSummaryCard")
    apply_fixed_policy(card, 84)
    card.setStyleSheet("QWidget#StatsSummaryCard { background: white; border: 1px solid rgba(0,0,0,0.06); border-radius: 12px; }")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(4)
    value_label = QLabel(value, card)
    value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 700; background: transparent;")
    title_label = QLabel(title, card)
    title_label.setStyleSheet(f"color: {MUTED}; font-size: 12px; font-weight: 500; background: transparent;")
    layout.addWidget(value_label, 0)
    layout.addWidget(title_label, 0)
    return card, value_label
