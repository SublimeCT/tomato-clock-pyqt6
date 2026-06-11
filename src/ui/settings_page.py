from __future__ import annotations

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.app_metadata import get_app_metadata
from src.core.pomodoro_engine import PomodoroEngine
from src.core.settings_store import SettingsStore
from src.ui.focus_type_dialog import FocusTypeDialog
from src.ui.settings_controls import StepperControl
from src.ui.ui_theme import BG, BORDER, MUTED, SUCCESS, TEXT, apply_fixed_policy, apply_panel_policy, rgba
from src.utils.icon_loader import load_app_icon


class SettingsPage(QWidget):
    def __init__(self, engine: PomodoroEngine, settings: SettingsStore):
        super().__init__()
        self._engine = engine
        self._settings = settings
        self._meta = get_app_metadata()
        self.setStyleSheet("SettingsPage { background: #FDF6F0; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 24)
        root.setSpacing(0)

        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 24, 24, 0)
        body_layout.setSpacing(20)
        body_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        durations = self._build_section("时长设置")
        durations_layout = durations.layout()
        assert durations_layout is not None
        self.focus_stepper = self._build_stepper(1, 180, self._settings.focus_minutes(), "分钟", self._on_focus_changed)
        self.short_break_stepper = self._build_stepper(1, 60, self._settings.short_break_minutes(), "分钟", self._on_short_break_changed)
        self.long_break_stepper = self._build_stepper(1, 90, self._settings.long_break_minutes(), "分钟", self._on_long_break_changed)
        self.long_break_every_stepper = self._build_stepper(1, 12, self._settings.long_break_every(), "次", self._on_long_break_every_changed)
        durations_layout.addWidget(self._setting_row("专注时长", "每次专注的分钟数", self.focus_stepper))
        durations_layout.addWidget(self._setting_row("短休息", "专注间的短暂休息", self.short_break_stepper))
        durations_layout.addWidget(self._setting_row("长休息", "多个番茄周期后", self.long_break_stepper))
        durations_layout.addWidget(self._setting_row("长休息间隔", "每 N 次专注后长休息", self.long_break_every_stepper))

        focus_type = self._build_section("专注类型")
        focus_type_layout = focus_type.layout()
        assert focus_type_layout is not None
        type_row = QWidget(self)
        type_row.setObjectName("SettingsRow")
        apply_fixed_policy(type_row, 76)
        type_row.setStyleSheet("QWidget#SettingsRow { background: transparent; border-top: 1px solid rgba(0,0,0,0.06); }")
        type_layout = QHBoxLayout(type_row)
        type_layout.setContentsMargins(20, 14, 20, 14)
        type_layout.setSpacing(12)
        icon_box = QLabel("▣", type_row)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setFixedSize(36, 36)
        icon_box.setStyleSheet(
            f"background: {rgba('#4F46E5', 0.10)}; color: #4F46E5; border-radius: 12px; font-size: 18px; font-weight: 700;"
        )
        info_box = QVBoxLayout()
        info_box.setContentsMargins(0, 0, 0, 0)
        info_box.setSpacing(2)
        info_box.addWidget(self._text_label("默认类型", 15, 500, TEXT))
        self.default_type_label = self._text_label(self._settings.default_focus_type(), 12, 400, MUTED)
        info_box.addWidget(self.default_type_label)
        type_info = QWidget(type_row)
        type_info.setLayout(info_box)
        manage_btn = QPushButton("管理", type_row)
        apply_fixed_policy(manage_btn, 36)
        manage_btn.setFixedWidth(76)
        manage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        manage_btn.setStyleSheet(
            f"QPushButton {{ background: white; color: #4A4A5A; border: 1px solid {BORDER}; border-radius: 8px; font-size: 13px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {BG}; }}"
        )
        manage_btn.clicked.connect(self.open_focus_type_manager)
        type_layout.addWidget(icon_box, 0)
        type_layout.addWidget(type_info, 1)
        type_layout.addWidget(manage_btn, 0)
        focus_type_layout.addWidget(type_row)

        about = self._build_section("")
        about_row = QWidget(self)
        apply_fixed_policy(about_row, 104)
        about_layout = QHBoxLayout(about_row)
        about_layout.setContentsMargins(20, 20, 20, 20)
        about_layout.setSpacing(16)
        app_icon = QLabel(about_row)
        app_icon.setFixedSize(64, 64)
        app_icon.setStyleSheet("background: transparent;")
        pixmap = load_app_icon("app-icon.png").pixmap(64, 64)
        if not pixmap.isNull():
            app_icon.setPixmap(pixmap)
        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(2)
        info.addWidget(self._text_label(self._meta.display_name, 18, 600, TEXT))
        info.addWidget(self._text_label(f"版本 {self._meta.version}", 13, 400, MUTED))
        repo = QLabel(f"<a href='{self._meta.repository_url}'>GitHub 仓库 -></a>", about_row)
        repo.setTextFormat(Qt.TextFormat.RichText)
        repo.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        repo.setOpenExternalLinks(False)
        repo.linkActivated.connect(lambda _: QDesktopServices.openUrl(QUrl(self._meta.repository_url)))
        repo.setStyleSheet(f"color: {SUCCESS}; font-size: 13px;")
        info.addWidget(repo)
        about_info = QWidget(about_row)
        about_info.setLayout(info)
        about_layout.addWidget(app_icon, 0)
        about_layout.addWidget(about_info, 1)
        about_layout_root = about.layout()
        assert about_layout_root is not None
        about_layout_root.addWidget(about_row)

        body_layout.addWidget(durations)
        body_layout.addWidget(focus_type)
        body_layout.addWidget(about)
        body_layout.addStretch(1)
        root.addWidget(body, 1)

    def _build_section(self, title: str) -> QWidget:
        section = QWidget(self)
        section.setObjectName("SettingsSection")
        apply_panel_policy(section)
        section.setStyleSheet("QWidget#SettingsSection { background: white; border: 1px solid rgba(0,0,0,0.06); border-radius: 18px; }")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if title:
            header = QLabel(title, section)
            apply_fixed_policy(header, 40)
            header.setContentsMargins(20, 16, 20, 8)
            header.setStyleSheet(f"color: {MUTED}; font-size: 13px; font-weight: 600; letter-spacing: 1px;")
            layout.addWidget(header)
        return section

    def _build_stepper(self, minimum: int, maximum: int, value: int, unit: str, callback) -> StepperControl:
        stepper = StepperControl(minimum, maximum, value, unit, self)
        stepper.valueChanged.connect(callback)
        return stepper

    def _setting_row(self, title: str, subtitle: str, field: QWidget) -> QWidget:
        row = QWidget(self)
        row.setObjectName("SettingsRow")
        apply_fixed_policy(row, 72)
        row.setStyleSheet("QWidget#SettingsRow { background: transparent; border-top: 1px solid rgba(0,0,0,0.06); }")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(12)
        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(2)
        info.addWidget(self._text_label(title, 15, 500, TEXT))
        info.addWidget(self._text_label(subtitle, 12, 400, MUTED))
        info_wrap = QWidget(row)
        info_wrap.setLayout(info)
        layout.addWidget(info_wrap, 1)
        layout.addWidget(field, 0)
        return row

    def _text_label(self, text: str, size: int, weight: int, color: str) -> QLabel:
        label = QLabel(text, self)
        label.setStyleSheet(f"color: {color}; font-size: {size}px; font-weight: {weight}; background: transparent;")
        return label

    def focus_durations(self) -> None:
        self.focus_stepper.setFocus()

    def open_focus_type_manager(self) -> None:
        dialog = FocusTypeDialog(settings=self._settings, current_type=self._settings.default_focus_type())
        if dialog.exec() == FocusTypeDialog.DialogCode.Accepted:
            picked = dialog.selected_type()
            self._engine.set_focus_type(picked)
            self.default_type_label.setText(picked)

    def _on_focus_changed(self, value: int) -> None:
        self._engine.set_focus_minutes(value)

    def _on_short_break_changed(self, value: int) -> None:
        self._engine.set_short_break_minutes(value)

    def _on_long_break_changed(self, value: int) -> None:
        self._engine.set_long_break_minutes(value)

    def _on_long_break_every_changed(self, value: int) -> None:
        self._engine.set_long_break_every(value)
