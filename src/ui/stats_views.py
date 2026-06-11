from __future__ import annotations

from datetime import date

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.ui.stats_common import BarPoint, ColumnBarChartWidget, HeatmapWidget
from src.ui.ui_theme import ACCENT, BG, BORDER, MUTED, SUCCESS, TEXT, apply_fixed_policy, apply_panel_policy, rgba


class _NavPanel(QWidget):
    prev_requested = pyqtSignal()
    next_requested = pyqtSignal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("StatsPanel")
        apply_panel_policy(self, 280)
        self.setStyleSheet("QWidget#StatsPanel { background: white; border: 1px solid rgba(0,0,0,0.06); border-radius: 18px; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)
        header = QHBoxLayout()
        header.setSpacing(12)
        self.title_label = QLabel(title, self)
        self.title_label.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: 600; background: transparent;")
        nav = QHBoxLayout()
        nav.setSpacing(12)
        self.prev_btn = self._nav_button("<")
        self.prev_btn.clicked.connect(self.prev_requested.emit)
        self.range_label = QLabel("", self)
        self.range_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.range_label.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 550; background: transparent;")
        self.next_btn = self._nav_button(">")
        self.next_btn.clicked.connect(self.next_requested.emit)
        nav.addWidget(self.prev_btn, 0)
        nav.addWidget(self.range_label, 0)
        nav.addWidget(self.next_btn, 0)
        header.addWidget(self.title_label, 0)
        header.addStretch(1)
        header.addLayout(nav)
        root.addLayout(header)
        self.body_layout = root

    def _nav_button(self, text: str) -> QPushButton:
        btn = QPushButton(text, self)
        btn.setObjectName("StatsNavButton")
        apply_fixed_policy(btn, 28)
        btn.setFixedWidth(28)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton#StatsNavButton {{ border: 1px solid {BORDER}; background: white; border-radius: 8px; color: {TEXT}; }}"
            f"QPushButton#StatsNavButton:hover {{ background: {BG}; }}"
        )
        return btn


class DayStatsPanel(_NavPanel):
    def __init__(self, parent=None):
        super().__init__("今日专注时段", parent)
        self.chart = ColumnBarChartWidget(self)
        self.chart.setMinimumHeight(208)
        self.body_layout.addWidget(self.chart, 1)

    def set_data(self, current_date: date, points: list[BarPoint], can_go_next: bool) -> None:
        self.range_label.setText(f"{current_date.year}年{current_date.month}月{current_date.day}日")
        self.next_btn.setEnabled(bool(can_go_next))
        self.chart.set_points(points)


class WeekStatsPanel(_NavPanel):
    def __init__(self, parent=None):
        super().__init__("本周专注", parent)
        self.chart = ColumnBarChartWidget(self)
        self.chart.setMinimumHeight(208)
        self.body_layout.addWidget(self.chart, 1)

    def set_data(self, start_day: date, end_day: date, points: list[BarPoint], can_go_next: bool) -> None:
        self.range_label.setText(f"{start_day.month}月{start_day.day}日 - {end_day.month}月{end_day.day}日")
        self.next_btn.setEnabled(bool(can_go_next))
        self.chart.set_points(points)


class MonthStatsPanel(_NavPanel):
    month_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__("月度概览", parent)
        self._cards: dict[int, QPushButton] = {}
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        for month in range(1, 13):
            btn = QPushButton(self)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setFixedHeight(66)
            btn.clicked.connect(lambda _checked=False, m=month: self.month_selected.emit(m))
            grid.addWidget(btn, (month - 1) // 4, (month - 1) % 4)
            self._cards[month] = btn
        self.body_layout.addLayout(grid)
        self.chart_title = QLabel(self)
        self.chart_title.setStyleSheet(f"color: {TEXT}; font-size: 15px; font-weight: 600; background: transparent;")
        self.chart = ColumnBarChartWidget(self)
        self.chart.setMinimumHeight(220)
        self.body_layout.addWidget(self.chart_title, 0)
        self.body_layout.addWidget(self.chart, 1)

    def set_data(
        self,
        year: int,
        current_month: int,
        month_counts: dict[int, int],
        month_minutes: dict[int, int],
        day_points: list[BarPoint],
        can_go_next: bool,
    ) -> None:
        self.range_label.setText(f"{year}年")
        self.next_btn.setEnabled(bool(can_go_next))
        for month, btn in self._cards.items():
            count = int(month_counts.get(month, 0))
            minutes = int(month_minutes.get(month, 0))
            if count > 0:
                subtitle = f"{count} 次 · {minutes // 60}h {minutes % 60}m" if minutes >= 60 else f"{count} 次 · {minutes}m"
            else:
                subtitle = "—"
            btn.setText(f"{month}月\n{subtitle}")
            btn.setChecked(month == current_month)
            btn.setStyleSheet(
                f"QPushButton {{ background: white; border: 1px solid {BORDER}; border-radius: 12px; color: {TEXT}; font-size: 13px; font-weight: 550; }}"
                f"QPushButton:hover {{ background: {BG}; }}"
                f"QPushButton:checked {{ background: {rgba(ACCENT, 0.08)}; border: 1px solid {rgba(ACCENT, 0.22)}; color: {ACCENT}; }}"
            )
        self.chart_title.setText(f"{year}年{current_month}月")
        self.chart.set_points(day_points)


class YearStatsPanel(_NavPanel):
    def __init__(self, parent=None):
        super().__init__("年度热力图", parent)
        self.heatmap = HeatmapWidget(self)
        legend_row = QWidget(self)
        legend_layout = QHBoxLayout(legend_row)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(6)
        less_label = QLabel("少", legend_row)
        less_label.setStyleSheet(f"color: {MUTED}; font-size: 11px; background: transparent;")
        more_label = QLabel("多", legend_row)
        more_label.setStyleSheet(f"color: {MUTED}; font-size: 11px; background: transparent;")
        legend_layout.addStretch(1)
        legend_layout.addWidget(less_label, 0)
        for color in ("#ECE6DE", rgba(SUCCESS, 0.24), rgba(SUCCESS, 0.42), rgba(SUCCESS, 0.62), SUCCESS):
            block = QLabel(legend_row)
            block.setFixedSize(14, 14)
            block.setStyleSheet(f"background: {color}; border-radius: 4px;")
            legend_layout.addWidget(block, 0)
        legend_layout.addWidget(more_label, 0)
        self.body_layout.addWidget(self.heatmap, 0)
        self.body_layout.addWidget(legend_row, 0)

    def set_data(self, year: int, counts: dict[str, int], can_go_next: bool) -> None:
        self.range_label.setText(f"{year}年")
        self.next_btn.setEnabled(bool(can_go_next))
        self.heatmap.set_data(year, counts)
