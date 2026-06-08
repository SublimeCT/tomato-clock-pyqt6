from __future__ import annotations

from datetime import date

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget


class MonthGrid(QWidget):
    month_changed = pyqtSignal(int, int)

    def __init__(self, year: int, parent=None):
        super().__init__(parent)
        today = date.today()
        self._today_year = int(today.year)
        self._today_month = int(today.month)
        self._year = min(int(year), self._today_year)
        self._month = int(today.month)
        self._counts: dict[int, int] = {}
        self._buttons: dict[int, QPushButton] = {}

        root = QGridLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setHorizontalSpacing(10)
        root.setVerticalSpacing(10)

        header = QWidget(self)
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)

        self.prev_btn = QPushButton("<", header)
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.setFixedSize(36, 36)
        self.prev_btn.clicked.connect(lambda: self.set_year(self._year - 1, emit=True))

        self.title = QLabel(header)
        self.title.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.title.setStyleSheet("font-size: 16px; font-weight: 700; color: rgba(0,0,0,0.78);")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_btn = QPushButton(">", header)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.setFixedSize(36, 36)
        self.next_btn.clicked.connect(lambda: self.set_year(self._year + 1, emit=True))

        for btn in (self.prev_btn, self.next_btn):
            btn.setStyleSheet(
                "QPushButton { border: 1px solid rgba(0,0,0,0.10); border-radius: 12px; background: rgba(255,255,255,0.80); font-weight: 700; }"
                "QPushButton:hover { border: 1px solid rgba(0,0,0,0.18); background: rgba(0,0,0,0.04); }"
                "QPushButton:pressed { background: rgba(0,0,0,0.08); }"
            )

        header_row.addWidget(self.prev_btn, 0)
        header_row.addWidget(self.title, 1)
        header_row.addWidget(self.next_btn, 0)
        root.addWidget(header, 0, 0, 1, 4)

        names = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
        for i in range(12):
            m = i + 1
            btn = QPushButton(names[i], self)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.clicked.connect(lambda _checked=False, month=m: self.set_month(month))
            btn.setStyleSheet(
                "QPushButton { border: 1px solid rgba(0,0,0,0.10); border-radius: 14px; background: rgba(255,255,255,0.80); font-weight: 650; }"
                "QPushButton:hover { border: 1px solid rgba(0,0,0,0.18); }"
                "QPushButton:checked { background: rgba(16,185,129,0.16); border: 1px solid rgba(16,185,129,0.24); }"
            )
            r = 1 + i // 4
            c = i % 4
            root.addWidget(btn, r, c)
            self._buttons[m] = btn

        self._set_month(self._month, emit=False)
        self._update_title()

    def set_year(self, year: int, *, emit: bool = False) -> None:
        year = min(int(year), self._today_year)
        self._year = year
        if emit:
            if self._year == self._today_year:
                self._month = self._today_month
            else:
                self._month = 1
        if self._year == self._today_year and self._month > self._today_month:
            self._month = self._today_month
        self._month = min(max(1, self._month), 12)
        self._update_visuals()
        self._update_title()
        if emit:
            self.month_changed.emit(self._year, self._month)

    def set_counts(self, counts_by_month: dict[int, int]) -> None:
        self._counts = dict(counts_by_month)
        self._update_visuals()

    def month(self) -> int:
        return self._month

    def set_month(self, month: int) -> None:
        self._set_month(month, emit=True)

    def _set_month(self, month: int, *, emit: bool) -> None:
        if month < 1 or month > 12:
            return
        if self._year >= self._today_year and int(month) > self._today_month:
            return
        self._month = int(month)
        for m, b in self._buttons.items():
            b.setChecked(m == self._month)
        self._update_visuals()
        self._update_title()
        if emit:
            self.month_changed.emit(self._year, self._month)

    def _update_title(self) -> None:
        self.title.setText(f"{self._year} 年")

    def _update_visuals(self) -> None:
        max_count = max(1, max(self._counts.values(), default=0))
        for m, btn in self._buttons.items():
            cnt = int(self._counts.get(m, 0))
            if cnt <= 0:
                btn.setText(f"{m}月")
            else:
                btn.setText(f"{m}月 {cnt}次")
            allowed = True
            if self._year >= self._today_year and m > self._today_month:
                allowed = False
            btn.setEnabled(bool(allowed))
            if not allowed:
                btn.setChecked(False)
            alpha = 0.06 if cnt <= 0 else (0.10 + 0.20 * (cnt / max_count))
            if allowed:
                btn.setStyleSheet(
                    "QPushButton {"
                    f"border: 1px solid rgba(0,0,0,0.10); border-radius: 14px; background: rgba(16,185,129,{alpha:.2f});"
                    "font-weight: 650; }"
                    "QPushButton:hover { border: 1px solid rgba(0,0,0,0.18); }"
                    "QPushButton:checked { background: rgba(16,185,129,0.24); border: 1px solid rgba(16,185,129,0.28); }"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton {"
                    "border: 1px solid rgba(0,0,0,0.08); border-radius: 14px; background: rgba(0,0,0,0.04);"
                    "font-weight: 650; color: rgba(0,0,0,0.35); }"
                )

        self.next_btn.setEnabled(self._year < self._today_year)


class YearGrid(QWidget):
    year_changed = pyqtSignal(int)

    def __init__(self, years: list[int], parent=None):
        super().__init__(parent)
        self._today_year = int(date.today().year)
        self._years_with_data = set(int(y) for y in years)
        self._year = self._today_year
        self._page_start = self._year - (self._year % 12)
        self._buttons: dict[int, QPushButton] = {}

        root = QGridLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setHorizontalSpacing(10)
        root.setVerticalSpacing(10)

        header = QWidget(self)
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)

        self.prev_btn = QPushButton("<", header)
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.setFixedSize(36, 36)
        self.prev_btn.clicked.connect(lambda: self.set_page_start(self._page_start - 12))

        self.title = QLabel(header)
        self.title.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.title.setStyleSheet("font-size: 16px; font-weight: 700; color: rgba(0,0,0,0.78);")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_btn = QPushButton(">", header)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.setFixedSize(36, 36)
        self.next_btn.clicked.connect(lambda: self.set_page_start(self._page_start + 12))

        for btn in (self.prev_btn, self.next_btn):
            btn.setStyleSheet(
                "QPushButton { border: 1px solid rgba(0,0,0,0.10); border-radius: 12px; background: rgba(255,255,255,0.80); font-weight: 700; }"
                "QPushButton:hover { border: 1px solid rgba(0,0,0,0.18); background: rgba(0,0,0,0.04); }"
                "QPushButton:pressed { background: rgba(0,0,0,0.08); }"
            )

        header_row.addWidget(self.prev_btn, 0)
        header_row.addWidget(self.title, 1)
        header_row.addWidget(self.next_btn, 0)
        root.addWidget(header, 0, 0, 1, 4)

        cols = 4
        for i in range(12):
            y = self._page_start + i
            btn = QPushButton(str(y), self)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.clicked.connect(lambda _checked=False, year=y: self.set_year(year))
            root.addWidget(btn, 1 + i // cols, i % cols)
            self._buttons[y] = btn

        self._update_buttons()
        self.set_year(self._year)

    def year(self) -> int:
        return self._year

    def set_years(self, years: list[int]) -> None:
        self._years_with_data = set(int(y) for y in years)
        self._update_buttons()

    def set_year(self, year: int) -> None:
        year = min(int(year), self._today_year)
        if year < self._page_start or year >= self._page_start + 12:
            self.set_page_start(year - (year % 12))
        self._year = year
        for y, b in self._buttons.items():
            b.setChecked(y == year)
        self._update_buttons()
        self.year_changed.emit(year)

    def set_page_start(self, start_year: int) -> None:
        max_page_start = self._today_year - (self._today_year % 12)
        self._page_start = min(int(start_year), int(max_page_start))
        items = sorted(self._buttons.items(), key=lambda x: x[0])
        buttons = [btn for _y, btn in items]
        self._buttons = {}
        for i, btn in enumerate(buttons):
            ny = self._page_start + i
            btn.setText(str(ny))
            try:
                btn.clicked.disconnect()
            except Exception:
                pass
            btn.clicked.connect(lambda _checked=False, year=ny: self.set_year(year))
            self._buttons[ny] = btn
        for y, b in self._buttons.items():
            b.setChecked(y == self._year)
        self._update_buttons()
        self._update_title()

    def _update_title(self) -> None:
        self.title.setText(f"{self._page_start} - {self._page_start + 11}")

    def _update_buttons(self) -> None:
        self._update_title()
        for y, btn in self._buttons.items():
            allowed = y <= self._today_year
            btn.setEnabled(bool(allowed))
            has_data = y in self._years_with_data
            if has_data:
                base_bg = "rgba(79,70,229,0.12)"
                base_border = "rgba(79,70,229,0.20)"
            else:
                base_bg = "rgba(255,255,255,0.80)"
                base_border = "rgba(0,0,0,0.10)"
            if not allowed:
                base_bg = "rgba(0,0,0,0.04)"
                base_border = "rgba(0,0,0,0.08)"
            btn.setStyleSheet(
                "QPushButton {"
                f"border: 1px solid {base_border}; border-radius: 14px; background: {base_bg}; font-weight: 650;"
                "}"
                "QPushButton:hover { border: 1px solid rgba(0,0,0,0.18); }"
                "QPushButton:checked { background: rgba(79,70,229,0.20); border: 1px solid rgba(79,70,229,0.28); }"
            )

        self.next_btn.setEnabled(self._page_start + 11 < self._today_year)
