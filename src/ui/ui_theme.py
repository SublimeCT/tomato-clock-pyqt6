from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QSizePolicy, QWidget

BG = "#FDF6F0"
SURFACE = "#FFFFFF"
SURFACE_SOFT = "#FFF9F5"
TEXT = "#1A1A2E"
TEXT_SECONDARY = "#4A4A5A"
MUTED = "#8C8C9A"
BORDER = "#E8E0D8"
ACCENT = "#E63946"
ACCENT_HOVER = "#D62828"
SUCCESS = "#2A9D8F"
WARN = "#F4A261"


def qcolor(color_hex: str, alpha: float = 1.0) -> QColor:
    """Return a QColor with an optional alpha multiplier."""
    color = QColor(color_hex)
    color.setAlphaF(max(0.0, min(1.0, float(alpha))))
    return color


def rgba(color_hex: str, alpha: float) -> str:
    """Return a stylesheet rgba() string from a hex color."""
    color = qcolor(color_hex, alpha)
    return f"rgba({color.red()},{color.green()},{color.blue()},{color.alpha()})"


def apply_fixed_policy(widget: QWidget, height: int | None = None) -> None:
    """Apply the Fixed vertical policy required by this project."""
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    if height is not None:
        widget.setFixedHeight(int(height))


def apply_panel_policy(widget: QWidget, minimum_height: int | None = None) -> None:
    """Apply the styled background attribute for card-like widgets."""
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    if minimum_height is not None:
        widget.setMinimumHeight(int(minimum_height))


def type_colors(color_hex: str) -> tuple[str, str, str]:
    """Build soft background, border and text colors for a focus type."""
    base = QColor(color_hex if QColor(color_hex).isValid() else "#4F46E5")
    return (
        f"rgba({base.red()},{base.green()},{base.blue()},26)",
        f"rgba({base.red()},{base.green()},{base.blue()},58)",
        base.name(),
    )


def macos_scrollbar_qss() -> str:
    """Return a subtle scrollbar style that approximates macOS overlay bars."""
    return (
        "QScrollBar:vertical { background: transparent; width: 10px; margin: 2px 2px 2px 0; border: none; }"
        "QScrollBar::handle:vertical { background: rgba(60,60,67,0.28); min-height: 32px; border-radius: 5px; border: none; }"
        "QScrollBar::handle:vertical:hover { background: rgba(60,60,67,0.40); }"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; background: transparent; }"
        "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; border: none; }"
        "QScrollBar:horizontal { background: transparent; height: 10px; margin: 0 2px 2px 2px; border: none; }"
        "QScrollBar::handle:horizontal { background: rgba(60,60,67,0.28); min-width: 32px; border-radius: 5px; border: none; }"
        "QScrollBar::handle:horizontal:hover { background: rgba(60,60,67,0.40); }"
        "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; border: none; background: transparent; }"
        "QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; border: none; }"
    )
