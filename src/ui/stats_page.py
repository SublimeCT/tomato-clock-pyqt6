from __future__ import annotations

from datetime import date

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QTextCharFormat
from PyQt6.QtWidgets import QCalendarWidget, QLabel, QListWidget, QVBoxLayout, QWidget

from src.core.session_store import SessionStore


class StatsPage(QWidget):
    def __init__(self, sessions: SessionStore):
        super().__init__()
        self._sessions = sessions

        self.setStyleSheet(
            "QCalendarWidget { border: 1px solid rgba(0,0,0,0.08); border-radius: 14px; background: rgba(255,255,255,0.75); }"
            "QListWidget { border: 1px solid rgba(0,0,0,0.08); border-radius: 14px; background: rgba(255,255,255,0.75); padding: 8px; }"
            "QLabel { color: rgba(0,0,0,0.70); font-size: 14px; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(False)
        self.calendar.selectionChanged.connect(self._on_selection_changed)

        self.summary_label = QLabel("", self)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.list_widget = QListWidget(self)

        root.addWidget(self.calendar)
        root.addWidget(self.summary_label)
        root.addWidget(self.list_widget, 1)

        self.refresh()

    def refresh(self) -> None:
        self._apply_heatmap()
        self._reload_list_for_selected_date()

    def _apply_heatmap(self) -> None:
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
        counts = self._sessions.counts_by_day()
        if not counts:
            return

        max_count = max(counts.values())
        max_count = max(1, int(max_count))

        for day_str, count in counts.items():
            try:
                year, month, day = [int(x) for x in day_str.split("-")]
            except Exception:
                continue
            qdate = QDate(year, month, day)
            intensity = min(1.0, count / max_count)
            color = QColor(255, 80, 80)
            bg = QColor(color)
            bg.setAlphaF(0.15 + (0.55 * intensity))
            fmt = QTextCharFormat()
            fmt.setBackground(bg)
            self.calendar.setDateTextFormat(qdate, fmt)

    def _on_selection_changed(self) -> None:
        self._reload_list_for_selected_date()

    def _reload_list_for_selected_date(self) -> None:
        qdate = self.calendar.selectedDate()
        selected = date(qdate.year(), qdate.month(), qdate.day())
        sessions = self._sessions.sessions_on(selected)

        self.list_widget.clear()
        for s in sessions:
            self.list_widget.addItem(f"{s.focus_type} · {s.minutes} 分钟 · {s.completed_at_iso[11:19]}")

        if selected == date.today():
            title = "今日完成"
        else:
            title = selected.isoformat()
        self.summary_label.setText(f"{title}: {len(sessions)} 个番茄钟")
