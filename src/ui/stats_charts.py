from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from PyQt6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QLineSeries, QValueAxis
from PyQt6.QtCore import QMargins, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget
from PyQt6.QtWidgets import QToolTip

from src.ui.ui_theme import ACCENT, MUTED, SUCCESS, TEXT, apply_fixed_policy, apply_panel_policy, rgba


class StatsModeBar(QWidget):
    mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        self._mode = "day"

        apply_fixed_policy(self, 44)
        self.setStyleSheet(
            "StatsModeBar { background: white; border: 1px solid rgba(0,0,0,0.06); border-radius: 12px; }"
            f"QPushButton {{ border: 0; background: transparent; font-size: 14px; font-weight: 600; color: {MUTED}; border-radius: 8px; }}"
            f"QPushButton:hover {{ color: {TEXT}; }}"
            f"QPushButton:checked {{ background: {rgba(SUCCESS, 0.10)}; color: {SUCCESS}; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        items = [("day", "日"), ("week", "周"), ("month", "月"), ("year", "年")]
        for key, label in items:
            btn = QPushButton(label, self)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda _checked=False, k=key: self.set_mode(k))
            layout.addWidget(btn, 1)
            self._buttons[key] = btn

        self.set_mode("day")

    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode not in self._buttons:
            return
        self._mode = mode
        for k, b in self._buttons.items():
            b.setChecked(k == mode)
        self.mode_changed.emit(mode)


@dataclass(frozen=True)
class SeriesPoint:
    axis_label: str
    tooltip_label: str
    minutes: int
    count: int


class BarLineChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._title = "统计"
        self._points: list[SeriesPoint] = []
        self.setMinimumHeight(240)
        apply_panel_policy(self, 240)
        self.setStyleSheet("BarLineChart { background: white; border: 1px solid rgba(0,0,0,0.06); border-radius: 18px; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self._title_label = QLabel(self)
        apply_fixed_policy(self._title_label, 28)
        self._title_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {TEXT};")

        self._chart = QChart()
        legend = self._chart.legend()
        if legend is not None:
            legend.hide()
        self._chart.setBackgroundVisible(False)
        self._chart.setDropShadowEnabled(False)
        self._chart.setMargins(QMargins(0, 0, 0, 0))
        self._chart.setBackgroundRoundness(0)

        self._chart_view = QChartView(self._chart, self)
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._chart_view.setStyleSheet("background: transparent;")
        self._chart_view.setContentsMargins(0, 0, 0, 0)

        self._empty_label = QLabel("暂无数据", self)
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: rgba(0,0,0,0.55); font-size: 14px;")

        self._body_stack = QStackedWidget(self)
        self._body_stack.addWidget(self._chart_view)
        self._body_stack.addWidget(self._empty_label)

        root.addWidget(self._title_label, 0)
        root.addWidget(self._body_stack, 1)

        self._bar_series = None
        self._line_series = None
        self._axis_x = None
        self._axis_y_minutes = None
        self._axis_y_count = None

        self._tooltip_hide_timer = QTimer(self)
        self._tooltip_hide_timer.setSingleShot(True)
        self._tooltip_hide_timer.timeout.connect(QToolTip.hideText)

        self._rebuild()

    def set_title(self, title: str) -> None:
        self._title = title
        self._rebuild()

    def set_points(self, points: Iterable[SeriesPoint]) -> None:
        self._points = list(points)
        self._rebuild()

    def _rebuild(self) -> None:
        self._title_label.setText(self._title)

        self._chart.removeAllSeries()
        for ax in list(self._chart.axes()):
            self._chart.removeAxis(ax)

        if not self._points:
            self._body_stack.setCurrentIndex(1)
            return

        self._body_stack.setCurrentIndex(0)

        categories = [p.axis_label for p in self._points]
        max_minutes = max(1, max(int(p.minutes) for p in self._points))
        max_count = max(1, max(int(p.count) for p in self._points))

        bar_set = QBarSet("时长")
        for p in self._points:
            bar_set.append(float(p.minutes))
        bar_set.setColor(QColor(SUCCESS))
        bar_set.setBorderColor(QColor(SUCCESS))

        bar_series = QBarSeries()
        bar_series.append(bar_set)

        line_series = QLineSeries()
        line_series.setName("次数")
        line_pen = QPen(QColor(ACCENT))
        line_pen.setWidth(2)
        line_series.setPen(line_pen)
        for i, p in enumerate(self._points):
            line_series.append(float(i), float(p.count))

        self._chart.addSeries(bar_series)
        self._chart.addSeries(line_series)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsVisible(True)
        axis_x.setLabelsFont(self._axis_font(12))
        axis_x.setLabelsColor(QColor(0, 0, 0, 140))
        axis_x.setLabelsAngle(0)
        if categories:
            axis_x.setRange(categories[0], categories[-1])

        axis_y_minutes = QValueAxis()
        axis_y_minutes.setRange(0, float(max_minutes))
        axis_y_minutes.setLabelsFont(self._axis_font(11))
        axis_y_minutes.setLabelsColor(QColor(0, 0, 0, 150))
        axis_y_minutes.setGridLineColor(QColor(0, 0, 0, 22))
        axis_y_minutes.setLinePenColor(QColor(0, 0, 0, 55))

        axis_y_count = QValueAxis()
        axis_y_count.setRange(0, float(max_count))
        axis_y_count.setLabelsFont(self._axis_font(11))
        axis_y_count.setLabelsColor(QColor(0, 0, 0, 150))
        axis_y_count.setGridLineVisible(False)
        axis_y_count.setLinePenColor(QColor(0, 0, 0, 55))

        self._chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        self._chart.addAxis(axis_y_minutes, Qt.AlignmentFlag.AlignLeft)
        self._chart.addAxis(axis_y_count, Qt.AlignmentFlag.AlignRight)

        bar_series.attachAxis(axis_x)
        bar_series.attachAxis(axis_y_minutes)
        line_series.attachAxis(axis_x)
        line_series.attachAxis(axis_y_count)

        if len(categories) >= 18:
            axis_x.setLabelsFont(self._axis_font(11))
            axis_x.setLabelsAngle(0)
        elif len(categories) >= 12:
            axis_x.setLabelsFont(self._axis_font(12))
            axis_x.setLabelsAngle(0)

        bar_series.hovered.connect(self._on_bar_hovered)
        line_series.hovered.connect(self._on_line_hovered)

        self._bar_series = bar_series
        self._line_series = line_series
        self._axis_x = axis_x
        self._axis_y_minutes = axis_y_minutes
        self._axis_y_count = axis_y_count

    def _axis_font(self, point_size: int) -> QFont:
        f = QFont()
        f.setPointSize(int(point_size))
        return f

    def _on_bar_hovered(self, status: bool, index: int, _barset) -> None:
        if not status:
            self._tooltip_hide_timer.start(220)
            return
        self._tooltip_hide_timer.stop()
        if index < 0 or index >= len(self._points):
            QToolTip.hideText()
            return
        p = self._points[index]
        QToolTip.showText(QCursor.pos(), f"{p.tooltip_label}\n时长: {p.minutes} 分钟\n次数: {p.count}", self._chart_view, msecShowTime=20000)

    def _on_line_hovered(self, point, state: bool) -> None:
        if not state:
            self._tooltip_hide_timer.start(220)
            return
        self._tooltip_hide_timer.stop()
        idx = int(round(float(point.x())))
        if idx < 0 or idx >= len(self._points):
            QToolTip.hideText()
            return
        p = self._points[idx]
        QToolTip.showText(QCursor.pos(), f"{p.tooltip_label}\n时长: {p.minutes} 分钟\n次数: {p.count}", self._chart_view, msecShowTime=20000)
