from __future__ import annotations

from datetime import date, datetime, timedelta

from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor, QTextCharFormat
from PyQt6.QtWidgets import QCalendarWidget, QStackedWidget, QVBoxLayout, QWidget

from src.core.session_store import SessionStore
from src.ui.stats_calendar_views import MonthGrid, YearGrid
from src.ui.stats_charts import BarLineChart, SeriesPoint, StatsModeBar
from src.ui.stats_contribution import YearContributionChart


class StatsPage(QWidget):
    def __init__(self, sessions: SessionStore):
        super().__init__()
        self._sessions = sessions
        self._mode = "day"
        self._selected_date = date.today()
        self._selected_year = date.today().year
        self._selected_month = date.today().month
        self._today = date.today()

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        self.mode_bar = StatsModeBar(self)
        self.mode_bar.mode_changed.connect(self._set_mode)

        self.calendar_stack = QStackedWidget(self)
        self.chart_stack = QStackedWidget(self)

        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(False)
        self.calendar.selectionChanged.connect(self._on_calendar_selected)
        self.calendar.setMaximumDate(QDate(self._today.year, self._today.month, self._today.day))
        self.calendar.setStyleSheet("QCalendarWidget { border: 1px solid rgba(0,0,0,0.08); border-radius: 14px; background: rgba(255,255,255,0.80); }")

        self.month_grid = MonthGrid(year=self._selected_year, parent=self)
        self.month_grid.month_changed.connect(self._on_month_selected)

        self.year_grid = YearGrid(years=self._sessions.years(), parent=self)
        self.year_grid.year_changed.connect(self._on_year_selected)

        self.calendar_stack.addWidget(self.calendar)
        self.calendar_stack.addWidget(self.month_grid)
        self.calendar_stack.addWidget(self.year_grid)

        self.day_chart = BarLineChart(self)
        self.week_chart = BarLineChart(self)
        self.month_chart = BarLineChart(self)
        self.year_contrib = YearContributionChart(self)

        self.chart_stack.addWidget(self.day_chart)
        self.chart_stack.addWidget(self.week_chart)
        self.chart_stack.addWidget(self.month_chart)
        self.chart_stack.addWidget(self.year_contrib)

        root.addWidget(self.mode_bar)
        root.addWidget(self.calendar_stack)
        root.addWidget(self.chart_stack, 1)

        self.refresh()

    def refresh(self) -> None:
        self._apply_calendar_heatmap()
        self._refresh_month_grid()
        self._refresh_year_grid()
        self._refresh_charts()

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        if mode in ("day", "week"):
            self.calendar_stack.setCurrentIndex(0)
            self.calendar.setSelectedDate(QDate(self._selected_year, self._selected_month, self._selected_date.day))
        elif mode == "month":
            self.calendar_stack.setCurrentIndex(1)
            self.month_grid.set_year(self._selected_year, emit=False)
        else:
            self.calendar_stack.setCurrentIndex(2)
            self.year_grid.set_year(self._selected_year)
        self._refresh_charts()

    def _on_calendar_selected(self) -> None:
        qd = self.calendar.selectedDate()
        picked = date(qd.year(), qd.month(), qd.day())
        if picked > self._today:
            self.calendar.setSelectedDate(QDate(self._today.year, self._today.month, self._today.day))
            picked = self._today
        self._selected_date = picked
        self._selected_year = self._selected_date.year
        self._selected_month = self._selected_date.month
        self._refresh_charts()

    def _on_month_selected(self, year: int, month: int) -> None:
        year = int(year)
        month = int(month)
        if (year, month) > (self._today.year, self._today.month):
            year = self._today.year
            month = self._today.month
        self._selected_year = year
        self._selected_month = month
        self._refresh_charts()

    def _on_year_selected(self, year: int) -> None:
        y = min(int(year), self._today.year)
        self._selected_year = y
        if self._selected_year == self._today.year and self._selected_month > self._today.month:
            self._selected_month = self._today.month
        self._refresh_charts()

    def _apply_calendar_heatmap(self) -> None:
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
        counts = self._sessions.counts_by_day()
        if not counts:
            return

        max_count = max(1, max(counts.values(), default=0))
        for day_str, count in counts.items():
            try:
                year, month, day = [int(x) for x in day_str.split("-")]
            except Exception:
                continue
            qdate = QDate(year, month, day)
            intensity = min(1.0, int(count) / max_count)
            bg = QColor("#10B981")
            bg.setAlphaF(0.10 + (0.55 * intensity))
            fmt = QTextCharFormat()
            fmt.setBackground(bg)
            self.calendar.setDateTextFormat(qdate, fmt)

    def _refresh_month_grid(self) -> None:
        counts = self._sessions.counts_by_day()
        counts_by_month: dict[int, int] = {}
        for key, v in counts.items():
            if not key.startswith(f"{self._selected_year:04d}-"):
                continue
            try:
                m = int(key[5:7])
            except Exception:
                continue
            counts_by_month[m] = counts_by_month.get(m, 0) + int(v)
        self.month_grid.set_year(self._selected_year, emit=False)
        self.month_grid.set_counts(counts_by_month)

    def _refresh_year_grid(self) -> None:
        self.year_grid.set_years(self._sessions.years())

    def _refresh_charts(self) -> None:
        if self._mode == "day":
            self.chart_stack.setCurrentIndex(0)
            self._refresh_day()
        elif self._mode == "week":
            self.chart_stack.setCurrentIndex(1)
            self._refresh_week()
        elif self._mode == "month":
            self.chart_stack.setCurrentIndex(2)
            self._refresh_month()
        else:
            self.chart_stack.setCurrentIndex(3)
            self._refresh_year()

    def _refresh_day(self) -> None:
        end_hour = 23
        if self._selected_date == self._today:
            end_hour = int(datetime.now().hour)

        minutes_by_hour = {h: 0 for h in range(end_hour + 1)}
        counts_by_hour = {h: 0 for h in range(end_hour + 1)}
        for s in self._sessions.sessions_on(self._selected_date):
            try:
                started = datetime.fromisoformat(s.started_at_iso)
            except Exception:
                continue
            h = int(started.hour)
            if h > end_hour:
                continue
            minutes_by_hour[h] += int(s.minutes)
            counts_by_hour[h] += 1

        points: list[SeriesPoint] = []
        for h in range(end_hour + 1):
            points.append(
                SeriesPoint(
                    axis_label=str(h),
                    tooltip_label=f"{h}点",
                    minutes=minutes_by_hour.get(h, 0),
                    count=counts_by_hour.get(h, 0),
                )
            )
        self.day_chart.set_title("日 · 小时(柱状:时长 / 折线:次数)")
        self.day_chart.set_points(points)

    def _refresh_week(self) -> None:
        start = self._selected_date - timedelta(days=self._selected_date.weekday())
        end = start + timedelta(days=6)
        if end > self._today:
            end = self._today
        sessions = self._sessions.sessions_between(start, end)
        minutes_by_day: dict[str, int] = {}
        counts_by_day: dict[str, int] = {}
        for s in sessions:
            key = s.completed_at_iso[:10]
            minutes_by_day[key] = minutes_by_day.get(key, 0) + int(s.minutes)
            counts_by_day[key] = counts_by_day.get(key, 0) + 1
        points: list[SeriesPoint] = []
        days = max(0, (end - start).days) + 1
        for i in range(days):
            d = start + timedelta(days=i)
            key = d.isoformat()
            points.append(
                SeriesPoint(
                    axis_label=str(i + 1),
                    tooltip_label=f"周{i + 1} · {d.isoformat()}",
                    minutes=minutes_by_day.get(key, 0),
                    count=counts_by_day.get(key, 0),
                )
            )
        self.week_chart.set_title("周 · 柱状(时长) + 折线(次数)")
        self.week_chart.set_points(points)

    def _refresh_month(self) -> None:
        first = date(self._selected_year, self._selected_month, 1)
        next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
        last = next_month - timedelta(days=1)
        if date(self._selected_year, self._selected_month, 1) == date(self._today.year, self._today.month, 1):
            last = min(last, self._today)
        sessions = self._sessions.sessions_between(first, last)
        minutes_by_day: dict[str, int] = {}
        counts_by_day: dict[str, int] = {}
        for s in sessions:
            key = s.completed_at_iso[:10]
            minutes_by_day[key] = minutes_by_day.get(key, 0) + int(s.minutes)
            counts_by_day[key] = counts_by_day.get(key, 0) + 1
        points: list[SeriesPoint] = []
        days = (last - first).days + 1
        for i in range(days):
            d = first + timedelta(days=i)
            key = d.isoformat()
            points.append(
                SeriesPoint(
                    axis_label=str(d.day),
                    tooltip_label=d.isoformat(),
                    minutes=minutes_by_day.get(key, 0),
                    count=counts_by_day.get(key, 0),
                )
            )
        self.month_chart.set_title("月 · 柱状(时长) + 折线(次数)")
        self.month_chart.set_points(points)

    def _refresh_year(self) -> None:
        counts = self._sessions.counts_by_day()
        filtered: dict[str, int] = {}
        prefix = f"{self._selected_year:04d}-"
        for k, v in counts.items():
            if k.startswith(prefix):
                filtered[k] = int(v)
        self.year_contrib.set_year(self._selected_year)
        self.year_contrib.set_counts(filtered)
