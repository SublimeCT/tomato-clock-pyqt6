from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import QSize, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QAbstractScrollArea, QHBoxLayout, QLabel, QPushButton, QScrollArea, QStyle, QVBoxLayout, QWidget

from src.core.pomodoro_engine import EngineState, PomodoroEngine
from src.core.settings_store import SettingsStore
from src.ui.update_notice import UpdateNoticeWidget
from src.ui.focus_widgets import ChevronRow, SessionDotsWidget, TimerRingWidget
from src.ui.ui_theme import ACCENT, ACCENT_HOVER, BORDER, MUTED, SUCCESS, TEXT, WARN, apply_fixed_policy, rgba


class _TemplateChip(QWidget):
    clicked = pyqtSignal()

    def __init__(self, emoji: str, name: str, meta: str, parent=None):
        super().__init__(parent)
        self.setObjectName("TemplateChip")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_fixed_policy(self, 54)
        self._checked = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)
        emoji_label = QLabel(emoji, self)
        emoji_label.setFixedSize(30, 30)
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_label.setStyleSheet("font-size: 22px; background: transparent;")
        info_wrap = QWidget(self)
        info_layout = QVBoxLayout(info_wrap)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(1)
        name_label = QLabel(name, info_wrap)
        name_label.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 600; background: transparent;")
        meta_label = QLabel(meta, info_wrap)
        meta_label.setStyleSheet(f"color: {MUTED}; font-size: 11px; font-weight: 400; background: transparent;")
        info_layout.addWidget(name_label)
        info_layout.addWidget(meta_label)
        layout.addWidget(emoji_label, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(info_wrap, 1)
        self._name_label = name_label
        self._meta_label = meta_label
        self.setMinimumWidth(118)
        self._refresh_style()

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self._refresh_style()

    def setChecked(self, checked: bool) -> None:
        self._checked = bool(checked)
        self._refresh_style()

    def isChecked(self) -> bool:
        return self._checked

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self.clicked.emit()
        super().mousePressEvent(event)

    def _refresh_style(self) -> None:
        if not self.isEnabled():
            border = ACCENT if self._checked else BORDER
            background = rgba(ACCENT, 0.08) if self._checked else "#F6F1EB"
            self.setStyleSheet(
                f"QWidget#TemplateChip {{ background: {background}; border: 1px solid {border}; border-radius: 12px; }}"
            )
            name_color = ACCENT if self._checked else "#9D9DA9"
            self._name_label.setStyleSheet(
                f"color: {name_color}; font-size: 13px; font-weight: 600; background: transparent;"
            )
            self._meta_label.setStyleSheet("color: #B6B0A9; font-size: 11px; font-weight: 400; background: transparent;")
            return
        border = ACCENT if self._checked else rgba(BORDER, 0.85)
        background = rgba(ACCENT, 0.08) if self._checked else "white"
        self.setStyleSheet(
            f"QWidget#TemplateChip {{ background: {background}; border: 1px solid {border}; border-radius: 12px; }}"
        )
        self._name_label.setStyleSheet(
            f"color: {ACCENT if self._checked else TEXT}; font-size: 13px; font-weight: 600; background: transparent;"
        )
        self._meta_label.setStyleSheet(f"color: {MUTED}; font-size: 11px; font-weight: 400; background: transparent;")


class FocusPage(QWidget):
    def __init__(
        self,
        engine: PomodoroEngine,
        settings: SettingsStore,
        on_open_focus_type_settings: Callable[[], None],
        on_open_focus_duration_settings: Callable[[], None],
    ):
        super().__init__()
        self._engine = engine
        self._settings = settings
        self._on_open_focus_type_settings = on_open_focus_type_settings
        self._on_open_focus_duration_settings = on_open_focus_duration_settings
        self.setStyleSheet("FocusPage { background: #FDF6F0; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 24)
        root.setSpacing(0)

        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 24, 24, 0)
        body_layout.setSpacing(16)
        body_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.session_dots = SessionDotsWidget(self)
        self.timer_ring = TimerRingWidget(self)

        self.break_hint = QLabel("", self)
        apply_fixed_policy(self.break_hint, 44)
        self.break_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.break_hint.setStyleSheet(
            f"background: {rgba(SUCCESS, 0.10)}; color: {SUCCESS}; border-radius: 12px;"
            "font-size: 14px; font-weight: 600;"
        )
        self.break_hint.hide()

        self.template_wrap = QWidget(self)
        template_layout = QVBoxLayout(self.template_wrap)
        template_layout.setContentsMargins(0, 0, 0, 0)
        template_layout.setSpacing(8)
        template_label = QLabel("快速切换模板", self.template_wrap)
        template_label.setStyleSheet("color: #8C8C9A; font-size: 12px; font-weight: 600; background: transparent;")
        self.template_scroll = QScrollArea(self.template_wrap)
        self.template_scroll.setFixedHeight(62)
        self.template_scroll.setWidgetResizable(True)
        self.template_scroll.setFrameShape(QAbstractScrollArea.Shape.NoFrame)
        self.template_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.template_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.template_container = QWidget(self.template_scroll)
        self.template_row = QHBoxLayout(self.template_container)
        self.template_row.setContentsMargins(0, 0, 0, 4)
        self.template_row.setSpacing(8)
        self.template_scroll.setWidget(self.template_container)
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_scroll)
        self._template_buttons: dict[str, _TemplateChip] = {}

        self.type_row = ChevronRow("专注类型", "学习", self)
        self.type_row.clicked.connect(self._open_type_settings)
        self.duration_row = ChevronRow("专注时长", "25 分钟", self)
        self.duration_row.clicked.connect(self._open_duration_settings)

        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.start_pause_button = QPushButton("开始", self)
        apply_fixed_policy(self.start_pause_button, 52)
        self.start_pause_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_pause_button.clicked.connect(self._engine.toggle)
        self.start_pause_button.setIconSize(QSize(18, 18))

        self.reset_button = QPushButton("↺", self)
        self.reset_button.setToolTip("重置")
        apply_fixed_policy(self.reset_button, 52)
        self.reset_button.setFixedWidth(52)
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.clicked.connect(self._engine.reset_focus)

        self._apply_action_styles(False, False)
        action_row.addWidget(self.start_pause_button, 1)
        action_row.addWidget(self.reset_button, 0)
        self.update_notice = UpdateNoticeWidget(self)

        body_layout.addWidget(self.session_dots, 0, Qt.AlignmentFlag.AlignHCenter)
        body_layout.addWidget(self.timer_ring, 0, Qt.AlignmentFlag.AlignHCenter)
        body_layout.addWidget(self.break_hint)
        body_layout.addWidget(self.template_wrap)
        body_layout.addWidget(self.type_row)
        body_layout.addWidget(self.duration_row)
        body_layout.addLayout(action_row)
        body_layout.addWidget(self.update_notice)
        body_layout.addStretch(1)
        root.addWidget(body, 1)

        self.reload_templates()
        self._engine.state_changed.connect(self._on_state_changed)
        self._engine.phase_finished.connect(self._on_phase_finished)
        self._on_state_changed(self._engine.state())

    def _apply_action_styles(self, running: bool, break_mode: bool) -> None:
        primary = WARN if running else SUCCESS if break_mode else ACCENT
        primary_hover = "#E8943A" if running else "#23867B" if break_mode else ACCENT_HOVER
        self.start_pause_button.setStyleSheet(
            f"QPushButton {{ background: {primary}; color: white; border: 0; border-radius: 18px;"
            "font-size: 17px; font-weight: 700; padding: 0 18px; }"
            f"QPushButton:hover {{ background: {primary_hover}; }}"
        )
        self.reset_button.setStyleSheet(
            "QPushButton { background: white; color: #4A4A5A; border: 1px solid rgba(0,0,0,0.08);"
            "border-radius: 12px; font-size: 20px; font-weight: 700; }"
            f"QPushButton:hover {{ background: {rgba(ACCENT, 0.08)}; color: {ACCENT}; }}"
        )

    def _open_type_settings(self) -> None:
        self._on_open_focus_type_settings()

    def _open_duration_settings(self) -> None:
        self._on_open_focus_duration_settings()

    def _on_state_changed(self, state: EngineState) -> None:
        phase_text = "专注" if state.phase == "focus" else "短休息" if state.phase == "short_break" else "长休息"
        self.timer_ring.set_content(state.time_str, phase_text)
        self.timer_ring.set_running(state.running, state.phase != "focus")
        self.timer_ring.set_progress(state.remaining_seconds, state.total_seconds)

        colors = self._settings.focus_type_colors()
        self.type_row.set_value(state.focus_type, colors.get(state.focus_type, "#4F46E5"))
        self.duration_row.set_value(f"{self._display_focus_minutes(state)} 分钟", "#8C8C9A")
        self.type_row.setEnabled(state.phase == "focus")
        self.duration_row.setEnabled(not state.running and state.phase == "focus")

        completed = state.completed_focus_count % max(1, state.long_break_every)
        self.session_dots.set_progress(completed, state.long_break_every)

        if state.running:
            self.start_pause_button.setText("暂停")
        elif state.phase == "focus":
            self.start_pause_button.setText("开始")
        else:
            self.start_pause_button.setText("开始休息")
        self._sync_start_button_icon(state.running)
        self._sync_template_buttons(state.template_id, state.phase == "focus" and not state.running)
        self._apply_action_styles(state.running, state.phase != "focus")

    def reload_templates(self) -> None:
        while self.template_row.count():
            item = self.template_row.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        self._template_buttons = {}
        templates = self._settings.templates()
        self.template_wrap.setVisible(bool(templates))
        for template in templates:
            button = _TemplateChip(template.emoji, template.name, f"{template.focus_minutes} 分钟 · {template.rounds} 轮", self.template_container)
            button.clicked.connect(lambda template_id=template.id: self._apply_template(template_id))
            self.template_row.addWidget(button, 0)
            self._template_buttons[template.id] = button
        self.template_row.addStretch(1)
        self._sync_template_buttons(self._settings.active_template_id(), not self._engine.state().running and self._engine.state().phase == "focus")

    def _apply_template(self, template_id: str) -> None:
        if self._engine.state().template_id == template_id:
            self._engine.clear_template()
            return
        template = self._settings.template_by_id(template_id)
        if template is None:
            return
        self._engine.apply_template(template)

    def _sync_template_buttons(self, active_id: str, enabled: bool) -> None:
        for template_id, button in self._template_buttons.items():
            button.setChecked(template_id == active_id)
            button.setEnabled(enabled)

    def _on_phase_finished(self, event) -> None:
        QTimer.singleShot(0, lambda: self._show_phase_hint(event.prompt_message))

    def _show_phase_hint(self, prompt_message: str) -> None:
        text = str(prompt_message).strip()
        if not text:
            return
        self.break_hint.setText(text)
        self.break_hint.show()
        QTimer.singleShot(3500, self.break_hint.hide)

    def _display_focus_minutes(self, state: EngineState) -> int:
        template = self._settings.template_by_id(state.template_id)
        if template is not None:
            return int(template.focus_minutes)
        return int(self._settings.focus_minutes())

    def _sync_start_button_icon(self, running: bool) -> None:
        style = self.style()
        if style is None:
            return
        icon = style.standardIcon(
            QStyle.StandardPixmap.SP_MediaPause if running else QStyle.StandardPixmap.SP_MediaPlay
        )
        self.start_pause_button.setIcon(icon)

    def show_update_notice(self, latest_version: str, release_url: str) -> None:
        self.update_notice.show_notice(latest_version, release_url)
