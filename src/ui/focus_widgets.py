from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from src.ui.ui_theme import ACCENT, BORDER, MUTED, SUCCESS, TEXT, apply_fixed_policy, type_colors


class SessionDotsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 4
        self._completed = 0
        apply_fixed_policy(self, 18)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self._row = row
        self._dots: list[QLabel] = []
        self.set_progress(0, 4)

    def set_progress(self, completed: int, total: int) -> None:
        self._completed = max(0, int(completed))
        self._total = max(1, int(total))
        self._ensure_dot_count(self._total)
        for index, dot in enumerate(self._dots):
            if index < self._completed:
                dot.setStyleSheet(f"background: {ACCENT}; border-radius: 4px;")
            elif index == min(self._completed, len(self._dots) - 1):
                dot.setStyleSheet(f"background: {ACCENT}; border-radius: 4px; border: 3px solid rgba(230,57,70,0.10);")
            else:
                dot.setStyleSheet("background: #E8E0D8; border-radius: 4px;")

    def _ensure_dot_count(self, total: int) -> None:
        while len(self._dots) < total:
            dot = QLabel(self)
            dot.setFixedSize(8, 8)
            self._row.addWidget(dot, 0, Qt.AlignmentFlag.AlignCenter)
            self._dots.append(dot)
        while len(self._dots) > total:
            dot = self._dots.pop()
            self._row.removeWidget(dot)
            dot.deleteLater()


class TimerRingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self._break_mode = False
        self.setMinimumSize(240, 240)
        self.setMaximumSize(240, 240)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._time_label = QLabel("25:00", self)
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setStyleSheet(f"color: {TEXT}; font-size: 56px; font-weight: 700;")

        self._phase_label = QLabel("专注", self)
        self._phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._phase_label.setStyleSheet(f"color: {MUTED}; font-size: 14px; font-weight: 600;")

        inner = QVBoxLayout()
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(4)
        inner.addStretch(1)
        inner.addWidget(self._time_label)
        inner.addWidget(self._phase_label)
        inner.addStretch(1)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addLayout(inner)

    def set_content(self, time_text: str, phase_text: str) -> None:
        self._time_label.setText(str(time_text))
        self._phase_label.setText(str(phase_text))

    def set_running(self, running: bool, break_mode: bool) -> None:
        color = SUCCESS if break_mode else ACCENT if running else TEXT
        self._time_label.setStyleSheet(f"color: {color}; font-size: 56px; font-weight: 700;")
        self._break_mode = bool(break_mode)
        self.update()

    def set_progress(self, remaining_seconds: int, total_seconds: int) -> None:
        total = max(1, int(total_seconds))
        remaining = max(0, min(int(remaining_seconds), total))
        self._progress = 1.0 - (float(remaining) / float(total))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(10, 10, self.width() - 20, self.height() - 20)
        pen_bg = QPen(QColor(BORDER), 6)
        painter.setPen(pen_bg)
        painter.drawEllipse(rect)

        color = QColor(SUCCESS if self._break_mode else ACCENT)
        pen_fg = QPen(color, 6)
        pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_fg)
        path = QPainterPath()
        path.arcMoveTo(rect, 90)
        path.arcTo(rect, 90, -360 * self._progress)
        painter.drawPath(path)
        painter.end()


class ChevronRow(QPushButton):
    clicked_value = pyqtSignal()

    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent)
        self._bg, self._border, self._text = type_colors("#4F46E5")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_fixed_policy(self, 64)
        self.setText("")
        self.setObjectName("FocusChevronRow")
        self.setStyleSheet(
            "QPushButton#FocusChevronRow {"
            "background: #FFFFFF; border: 1px solid rgba(0,0,0,0.06); border-radius: 12px; }"
            "QPushButton#FocusChevronRow:hover { background: rgba(230,57,70,0.05); }"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 14, 16, 14)
        row.setSpacing(10)

        self.title_label = QLabel(title, self)
        self.title_label.setStyleSheet(f"color: {TEXT}; font-size: 15px; font-weight: 500;")
        self.value_pill = QLabel(self)
        self.value_pill.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.value_pill.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.value_pill.setFixedHeight(28)
        self.value_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chevron = QLabel(">", self)
        self.chevron.setStyleSheet(f"color: {MUTED}; font-size: 16px; font-weight: 700;")

        row.addWidget(self.title_label, 0)
        row.addStretch(1)
        row.addWidget(self.value_pill, 0)
        row.addWidget(self.chevron, 0)
        self.set_value(value)

    def set_value(self, value: str, color_hex: str = "#4F46E5") -> None:
        bg, border, text = type_colors(color_hex)
        self.value_pill.setText(str(value))
        self.value_pill.setStyleSheet(
            f"background: {bg}; border: 1px solid {border}; color: {text};"
            "border-radius: 14px; padding: 0 12px;"
            "font-size: 13px; font-weight: 600;"
        )
