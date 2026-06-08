from __future__ import annotations

from datetime import date, timedelta

from PyQt6.QtCharts import QChart, QChartView, QScatterSeries, QValueAxis
from PyQt6.QtCore import QMargins, QTimer, QSize, Qt
from PyQt6.QtGui import QColor, QCursor, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QStackedWidget, QToolTip, QVBoxLayout, QWidget


class YearContributionChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._year = date.today().year
        self._counts_by_day: dict[str, int] = {}
        self.setMinimumHeight(190)
        self.setStyleSheet(
            "YearContributionChart { background: rgba(255,255,255,0.85); border: 1px solid rgba(0,0,0,0.08); border-radius: 14px; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self._title_label = QLabel(self)
        self._title_label.setStyleSheet("font-size: 15px; font-weight: 700; color: rgba(0,0,0,0.86);")

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

        self._point_to_day: dict[tuple[int, int], str] = {}
        self._axis_x = None
        self._axis_y = None
        self._cols = 0
        self._tooltip_hide_timer = QTimer(self)
        self._tooltip_hide_timer.setSingleShot(True)
        self._tooltip_hide_timer.timeout.connect(QToolTip.hideText)

        self._rebuild()


    def set_year(self, year: int) -> None:
        self._year = int(year)
        self._rebuild()

    def set_counts(self, counts_by_day: dict[str, int]) -> None:
        self._counts_by_day = dict(counts_by_day)
        self._rebuild()

    def sizeHint(self) -> QSize:
        return QSize(520, 200)

    def _rebuild(self) -> None:
        self._title_label.setText(f"年 · 贡献图 ({self._year})")

        self._chart.removeAllSeries()
        for ax in list(self._chart.axes()):
            self._chart.removeAxis(ax)

        self._point_to_day = {}

        start = date(self._year, 1, 1)
        end = date(self._year, 12, 31)
        start = start - timedelta(days=(start.weekday() + 1) % 7)
        max_weeks = int((end - start).days / 7) + 1
        self._cols = int(max_weeks)

        if not self._counts_by_day:
            self._body_stack.setCurrentIndex(1)
            return
        max_count = max(1, max((int(v) for v in self._counts_by_day.values()), default=0))

        self._body_stack.setCurrentIndex(0)

        palette = [
            QColor(0, 0, 0, 18),
            QColor(16, 185, 129, 80),
            QColor(16, 185, 129, 120),
            QColor(16, 185, 129, 160),
            QColor(16, 185, 129, 210),
        ]

        def level_for(v: int) -> int:
            if v <= 0:
                return 0
            t = min(1.0, float(v) / float(max_count))
            if t <= 0.25:
                return 1
            if t <= 0.50:
                return 2
            if t <= 0.75:
                return 3
            return 4

        series_by_level: dict[int, QScatterSeries] = {}
        for lvl in range(5):
            s = QScatterSeries()
            s.setMarkerSize(9.2)
            try:
                s.setMarkerShape(QScatterSeries.MarkerShape.MarkerShapeRectangle)
            except Exception:
                pass
            s.setColor(palette[lvl])
            s.setBorderColor(QColor(0, 0, 0, 0))
            s.hovered.connect(self._on_point_hovered)
            series_by_level[lvl] = s
            self._chart.addSeries(s)

        d = start
        while d <= end:
            key = d.isoformat()
            v = int(self._counts_by_day.get(key, 0))
            col = int((d - start).days // 7)
            row = int((d.weekday() + 1) % 7)
            lvl = level_for(v)
            series_by_level[lvl].append(float(col), float(row))
            self._point_to_day[(col, row)] = key
            d += timedelta(days=1)

        axis_x = QValueAxis()
        axis_x.setRange(-0.5, float(max_weeks) - 0.5)
        axis_x.setTickCount(min(max_weeks + 1, 14))
        axis_x.setLabelsVisible(False)
        axis_x.setGridLineVisible(False)
        axis_x.setLinePen(QPen(QColor(0, 0, 0, 0)))
        axis_x.setVisible(False)

        axis_y = QValueAxis()
        axis_y.setRange(-0.5, 6.5)
        axis_y.setTickCount(8)
        axis_y.setLabelsVisible(False)
        axis_y.setGridLineVisible(False)
        axis_y.setLinePen(QPen(QColor(0, 0, 0, 0)))
        axis_y.setVisible(False)

        self._chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        self._chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        for s in series_by_level.values():
            s.attachAxis(axis_x)
            s.attachAxis(axis_y)

        self._axis_x = axis_x
        self._axis_y = axis_y
        QTimer.singleShot(0, self._sync_square_grid)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        QTimer.singleShot(0, self._sync_square_grid)

    def _sync_square_grid(self) -> None:
        if self._axis_x is None or self._axis_y is None:
            return
        if self._cols <= 0:
            return

        plot = self._chart.plotArea()
        if plot.width() <= 1 or plot.height() <= 1:
            return

        x_span = float(self._cols)
        target_y_span = (plot.height() * x_span) / max(1.0, plot.width())
        target_y_span = max(7.0, float(target_y_span))
        pad = (target_y_span - 7.0) / 2.0

        self._axis_x.setRange(-0.5, float(self._cols) - 0.5)
        self._axis_y.setRange(-0.5 - pad, 6.5 + pad)

    def _on_point_hovered(self, point, state: bool) -> None:
        if not state:
            self._tooltip_hide_timer.start(220)
            return
        self._tooltip_hide_timer.stop()
        col = int(round(float(point.x())))
        row = int(round(float(point.y())))
        key = self._point_to_day.get((col, row))
        if not key:
            QToolTip.hideText()
            return
        v = int(self._counts_by_day.get(key, 0))
        QToolTip.showText(QCursor.pos(), f"{key}\n次数: {v}", self._chart_view, msecShowTime=20000)
