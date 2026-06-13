from __future__ import annotations

from datetime import date, datetime, timedelta
from calendar import monthrange

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractScrollArea, QHBoxLayout, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from src.core.session_store import FocusSession, SessionStore
from src.ui.stats_common import BarPoint, StatsModeBar, make_card
from src.ui.stats_views import DayStatsPanel, MonthStatsPanel, SessionTimelineItem, WeekStatsPanel, YearStatsPanel
from src.ui.ui_theme import ACCENT, SUCCESS, WARN


class StatsPage(QWidget):
    def __init__(self, sessions: SessionStore):
        super().__init__()
        self._sessions = sessions
        self._mode = "day"
        self._selected_date = date.today()
        self._selected_year = date.today().year
        self._selected_month = date.today().month
        self._today = date.today()
        self.setStyleSheet("StatsPage { background: #FDF6F0; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 24)
        root.setSpacing(0)

        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 24, 24, 0)
        body_layout.setSpacing(16)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(12)
        self.today_count_card = make_card("今日专注", "0", ACCENT, self)
        self.today_minutes_card = make_card("今日时长", "0m", SUCCESS, self)
        self.week_count_card = make_card("本周专注", "0", WARN, self)
        summary_row.addWidget(self.today_count_card[0], 1)
        summary_row.addWidget(self.today_minutes_card[0], 1)
        summary_row.addWidget(self.week_count_card[0], 1)

        self.mode_bar = StatsModeBar(self)
        self.mode_bar.mode_changed.connect(self._set_mode)
        self.view_stack = QStackedWidget(self)
        self.view_stack.setMinimumHeight(500)

        self.day_view = DayStatsPanel(self)
        self.day_view.prev_requested.connect(self._go_prev_day)
        self.day_view.next_requested.connect(self._go_next_day)

        self.week_view = WeekStatsPanel(self)
        self.week_view.prev_requested.connect(self._go_prev_week)
        self.week_view.next_requested.connect(self._go_next_week)

        self.month_view = MonthStatsPanel(self)
        self.month_view.prev_requested.connect(self._go_prev_year)
        self.month_view.next_requested.connect(self._go_next_year)
        self.month_view.month_selected.connect(self._on_month_selected)

        self.year_view = YearStatsPanel(self)
        self.year_view.prev_requested.connect(self._go_prev_year)
        self.year_view.next_requested.connect(self._go_next_year)

        self.view_stack.addWidget(self.day_view)
        self.view_stack.addWidget(self.week_view)
        self.view_stack.addWidget(self.month_view)
        self.view_stack.addWidget(self.year_view)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QAbstractScrollArea.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(self.view_stack)

        body_layout.addLayout(summary_row)
        body_layout.addWidget(self.mode_bar)
        body_layout.addWidget(self.scroll_area, 1)
        root.addWidget(body, 1)
        self.refresh()

    def refresh(self) -> None:
        self._refresh_summary()
        self._refresh_current_view()

    def _refresh_summary(self) -> None:
        today_sessions = self._sessions.sessions_on(self._today)
        today_minutes = sum(int(s.minutes) for s in today_sessions)
        week_start = self._today - timedelta(days=self._today.weekday())
        week_sessions = self._sessions.sessions_between(week_start, self._today)
        self.today_count_card[1].setText(str(len(today_sessions)))
        self.today_minutes_card[1].setText(f"{today_minutes // 60}h {today_minutes % 60}m" if today_minutes >= 60 else f"{today_minutes}m")
        self.week_count_card[1].setText(str(len(week_sessions)))

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        self.view_stack.setCurrentIndex({"day": 0, "week": 1, "month": 2, "year": 3}[mode])
        self._refresh_current_view()

    def _on_month_selected(self, month: int) -> None:
        year = self._selected_year
        month = int(month)
        if (year, month) > (self._today.year, self._today.month):
            year = self._today.year
            month = self._today.month
        self._selected_year = year
        self._selected_month = month
        self._mode = "month"
        self.mode_bar.set_mode("month")

    def _refresh_current_view(self) -> None:
        if self._mode == "day":
            self._refresh_day()
        elif self._mode == "week":
            self._refresh_week()
        elif self._mode == "month":
            self._refresh_month()
        else:
            self._refresh_year()

    def _refresh_day(self) -> None:
        end_hour = 23
        if self._selected_date == self._today:
            end_hour = int(datetime.now().hour)
        day_sessions: list[tuple[datetime, datetime, FocusSession]] = []
        minutes_by_hour = {h: 0 for h in range(end_hour + 1)}
        for s in self._sessions.sessions_on(self._selected_date):
            try:
                started = datetime.fromisoformat(s.started_at_iso)
                completed = datetime.fromisoformat(s.completed_at_iso)
            except Exception:
                continue
            h = int(started.hour)
            if h > end_hour:
                continue
            minutes_by_hour[h] += int(s.minutes)
            day_sessions.append((started, completed, s))
        points: list[BarPoint] = []
        current_hour = int(datetime.now().hour) if self._selected_date == self._today else -1
        for h in range(end_hour + 1):
            points.append(BarPoint(label=str(h), value=minutes_by_hour.get(h, 0), hint=f"{h}点\n时长: {minutes_by_hour.get(h, 0)} 分钟", accent=h == current_hour))
        colors = self._sessions_on_day_colors(day_sessions)
        items = [
            SessionTimelineItem(
                time_range=f"{started.strftime('%H:%M')} ~ {completed.strftime('%H:%M')}",
                title=str(session.focus_type),
                minutes=int(session.minutes),
                template_name=str(getattr(session, "template_name", "")).strip(),
                color_hex=colors.get(str(session.focus_type), "#4F46E5"),
            )
            for started, completed, session in sorted(day_sessions, key=lambda item: item[0])
        ]
        self.day_view.set_data(self._selected_date, points, items, self._selected_date < self._today)

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
        points: list[BarPoint] = []
        days = max(0, (end - start).days) + 1
        for i in range(7):
            d = start + timedelta(days=i)
            key = d.isoformat()
            minutes = minutes_by_day.get(key, 0) if i < days else 0
            count = counts_by_day.get(key, 0) if i < days else 0
            points.append(BarPoint(label=["一", "二", "三", "四", "五", "六", "日"][i], value=minutes, hint=f"{d.isoformat()}\n时长: {minutes} 分钟\n次数: {count}", accent=d == self._today))
        self.week_view.set_data(start, end, points, end < self._today)

    def _refresh_month(self) -> None:
        month_counts: dict[int, int] = {}
        month_minutes: dict[int, int] = {}
        for session in self._sessions.all_sessions():
            try:
                done = datetime.fromisoformat(session.completed_at_iso)
            except Exception:
                continue
            if done.year != self._selected_year:
                continue
            month_counts[done.month] = month_counts.get(done.month, 0) + 1
            month_minutes[done.month] = month_minutes.get(done.month, 0) + int(session.minutes)
        first = date(self._selected_year, self._selected_month, 1)
        next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
        last = next_month - timedelta(days=1)
        if self._selected_year == self._today.year and self._selected_month == self._today.month:
            last = min(last, self._today)
        minutes_by_day: dict[str, int] = {}
        for session in self._sessions.sessions_between(first, last):
            key = session.completed_at_iso[:10]
            minutes_by_day[key] = minutes_by_day.get(key, 0) + int(session.minutes)
        day_points: list[BarPoint] = []
        days = (last - first).days + 1
        for index in range(days):
            current_day = first + timedelta(days=index)
            key = current_day.isoformat()
            minutes = minutes_by_day.get(key, 0)
            day_points.append(
                BarPoint(
                    label=str(current_day.day),
                    value=minutes,
                    hint=f"{key}\n时长: {minutes} 分钟",
                    accent=current_day == self._today,
                )
            )
        self.month_view.set_data(
            self._selected_year,
            self._selected_month,
            month_counts,
            month_minutes,
            day_points,
            self._selected_year < self._today.year,
        )

    def _refresh_year(self) -> None:
        counts = self._sessions.counts_by_day()
        filtered: dict[str, int] = {}
        start_day, end_day = self._year_period()
        for k, v in counts.items():
            if start_day.isoformat() <= k <= end_day.isoformat():
                filtered[k] = int(v)
        self.year_view.set_data(start_day, end_day, filtered, end_day < self._today)

    def _go_prev_day(self) -> None:
        self._selected_date -= timedelta(days=1)
        self._selected_year = self._selected_date.year
        self._selected_month = self._selected_date.month
        self._refresh_day()

    def _go_next_day(self) -> None:
        if self._selected_date >= self._today:
            return
        self._selected_date += timedelta(days=1)
        self._selected_year = self._selected_date.year
        self._selected_month = self._selected_date.month
        self._refresh_day()

    def _go_prev_week(self) -> None:
        self._selected_date -= timedelta(days=7)
        self._selected_year = self._selected_date.year
        self._selected_month = self._selected_date.month
        self._refresh_week()

    def _go_next_week(self) -> None:
        candidate = self._selected_date + timedelta(days=7)
        if candidate > self._today:
            candidate = self._today
        if candidate == self._selected_date:
            return
        self._selected_date = candidate
        self._selected_year = self._selected_date.year
        self._selected_month = self._selected_date.month
        self._refresh_week()

    def _go_prev_year(self) -> None:
        self._selected_year -= 1
        self._refresh_current_view()

    def _go_next_year(self) -> None:
        if self._selected_year >= self._today.year:
            return
        self._selected_year += 1
        if self._selected_year == self._today.year and self._selected_month > self._today.month:
            self._selected_month = self._today.month
        self._refresh_current_view()

    def _sessions_on_day_colors(self, day_sessions: list[tuple[datetime, datetime, FocusSession]]) -> dict[str, str]:
        colors = {
            "学习": "#4F46E5",
            "阅读": "#10B981",
            "健身": "#F97316",
            "工作": "#0EA5E9",
            "专注": "#7C3AED",
            "冥想": "#14B8A6",
            "烹饪": "#F59E0B",
            "瑜伽": "#EC4899",
        }
        for _started, _completed, session in day_sessions:
            focus_type = str(getattr(session, "focus_type", "")).strip()
            if focus_type and focus_type not in colors:
                colors[focus_type] = "#4F46E5"
        return colors

    def _year_period(self) -> tuple[date, date]:
        end_day = self._same_month_day(self._selected_year, self._today)
        if end_day > self._today:
            end_day = self._today
        start_day = self._same_month_day(end_day.year - 1, end_day)
        return start_day, end_day

    def _same_month_day(self, target_year: int, source_day: date) -> date:
        last_day = monthrange(target_year, source_day.month)[1]
        return date(target_year, source_day.month, min(source_day.day, last_day))
