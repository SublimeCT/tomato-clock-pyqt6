from __future__ import annotations

import sys

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.pomodoro_engine import PomodoroEngine
from src.core.settings_store import SettingsStore
from src.ui.focus_type_dialog import FocusTypeDialog
from src.utils.icon_loader import load_app_icon


class LogoLabel(QLabel):
    def mouseDoubleClickEvent(self, event) -> None:
        QDesktopServices.openUrl(QUrl("https://sublimect.github.io/tomato-clock-pyqt6/"))
        super().mouseDoubleClickEvent(event)


class SettingsPage(QWidget):
    def __init__(self, engine: PomodoroEngine, settings: SettingsStore):
        super().__init__()
        self._engine = engine
        self._settings = settings
        self.setObjectName("SettingsPage")

        app_version = self._read_project_version()
        self.setStyleSheet(
            "QGroupBox { border: 1px solid rgba(0,0,0,0.08); border-radius: 14px; background: rgba(255,255,255,0.70); margin-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: rgba(0,0,0,0.65); }"
            "QLabel { color: rgba(0,0,0,0.75); }"
            "QPushButton#ManageFocusTypeButton {"
            "  border: 1px solid rgba(79,70,229,0.26);"
            "  background: rgba(79,70,229,0.12);"
            "  color: rgba(0,0,0,0.84);"
            "  border-radius: 14px;"
            "  font-size: 15px;"
            "  font-weight: 750;"
            "  padding: 10px 14px;"
            "  text-align: center;"
            "}"
            "QPushButton#ManageFocusTypeButton:hover { background: rgba(79,70,229,0.18); }"
            "QPushButton#ManageFocusTypeButton:pressed { background: rgba(79,70,229,0.24); }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        durations_group = QGroupBox("时长", self)
        durations_form = QFormLayout(durations_group)
        durations_form.setContentsMargins(14, 14, 14, 14)
        durations_form.setHorizontalSpacing(12)
        durations_form.setVerticalSpacing(10)

        self.focus_spin = QSpinBox(self)
        self.focus_spin.setRange(1, 180)
        self.focus_spin.setValue(self._settings.focus_minutes())
        self.focus_spin.setSuffix(" 分钟")
        self.focus_spin.valueChanged.connect(self._on_focus_changed)
        self.focus_spin.setFixedWidth(160)

        self.short_break_spin = QSpinBox(self)
        self.short_break_spin.setRange(1, 60)
        self.short_break_spin.setValue(self._settings.short_break_minutes())
        self.short_break_spin.setSuffix(" 分钟")
        self.short_break_spin.valueChanged.connect(self._on_short_break_changed)
        self.short_break_spin.setFixedWidth(160)

        self.long_break_spin = QSpinBox(self)
        self.long_break_spin.setRange(1, 90)
        self.long_break_spin.setValue(self._settings.long_break_minutes())
        self.long_break_spin.setSuffix(" 分钟")
        self.long_break_spin.valueChanged.connect(self._on_long_break_changed)
        self.long_break_spin.setFixedWidth(160)

        self.long_break_every_spin = QSpinBox(self)
        self.long_break_every_spin.setRange(1, 12)
        self.long_break_every_spin.setValue(self._settings.long_break_every())
        self.long_break_every_spin.setSuffix(" 次")
        self.long_break_every_spin.valueChanged.connect(self._on_long_break_every_changed)
        self.long_break_every_spin.setFixedWidth(160)

        durations_form.addRow("默认专注时长", self._right_align_field(self.focus_spin, parent=durations_group))
        durations_form.addRow("短休息时长", self._right_align_field(self.short_break_spin, parent=durations_group))
        durations_form.addRow("长休息时长", self._right_align_field(self.long_break_spin, parent=durations_group))
        durations_form.addRow("长休息所需次数", self._right_align_field(self.long_break_every_spin, parent=durations_group))

        focus_type_group = QGroupBox("专注类型", self)
        focus_type_layout = QVBoxLayout(focus_type_group)
        focus_type_layout.setContentsMargins(14, 14, 14, 14)
        focus_type_layout.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(10)
        title = QLabel("默认类型", focus_type_group)
        title.setStyleSheet("color: rgba(0,0,0,0.55);")
        self.default_type_label = QLabel(self._settings.default_focus_type(), focus_type_group)
        self.default_type_label.setStyleSheet("font-weight: 650;")
        row.addWidget(title)
        row.addStretch(1)
        row.addWidget(self.default_type_label)

        manage_btn = QPushButton("管理专注类型", focus_type_group)
        manage_btn.setObjectName("ManageFocusTypeButton")
        manage_btn.setText("🧩 管理专注类型")
        manage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        manage_btn.setFixedHeight(42)
        manage_btn.clicked.connect(self.open_focus_type_manager)

        focus_type_layout.addLayout(row)
        focus_type_layout.addWidget(manage_btn)

        about_group = QGroupBox("关于", self)
        about_layout = QVBoxLayout(about_group)
        about_layout.setContentsMargins(14, 18, 14, 14)
        about_layout.setSpacing(10)
        app_icon_label = LogoLabel(about_group)
        pixmap = load_app_icon("app-icon.png").pixmap(128, 128)
        if not pixmap.isNull():
            app_icon_label.setPixmap(pixmap)
            app_icon_label.setFixedSize(128, 128)
            app_icon_label.setScaledContents(False)
        app_icon_label.setStyleSheet("background: transparent;")
        app_icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        about_layout.addWidget(app_icon_label, 0, Qt.AlignmentFlag.AlignHCenter)
        title_label = QLabel(f"番茄专注(v{app_version})", about_group)
        title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: rgba(0,0,0,0.86);")
        about_layout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
        about_layout.addWidget(QLabel("状态栏番茄钟 / 专注 / 统计", about_group), 0, Qt.AlignmentFlag.AlignHCenter)
        repo_label = QLabel(about_group)
        repo_label.setTextFormat(Qt.TextFormat.RichText)
        repo_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        repo_label.setOpenExternalLinks(True)
        repo_label.setWordWrap(True)
        repo_label.setText('<p style="text-align: center;">开源仓库: <a href="https://github.com/SublimeCT/tomato-clock-pyqt6">https://github.com/SublimeCT/tomato-clock-pyqt6</a></p>')
        about_layout.addWidget(repo_label)

        root.addWidget(durations_group)
        root.addWidget(focus_type_group)
        root.addWidget(about_group)
        root.addStretch(1)

    def _right_align_field(self, field: QWidget, *, parent: QWidget) -> QWidget:
        wrap = QWidget(parent)
        row = QHBoxLayout(wrap)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addStretch(1)
        row.addWidget(field, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return wrap

    def focus_durations(self) -> None:
        self.focus_spin.setFocus()

    def _read_project_version(self) -> str:
        try:
            import tomllib
        except Exception:
            return "0.0.0"
        try:
            from pathlib import Path

            if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                pyproject_path = Path(getattr(sys, "_MEIPASS")) / "pyproject.toml"
            else:
                pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"

            if pyproject_path.exists():
                raw = pyproject_path.read_bytes()
                data = tomllib.loads(raw.decode("utf-8"))
                version = data.get("project", {}).get("version", None)
                if isinstance(version, str) and version.strip():
                    return version.strip()
        except Exception:
            pass

        try:
            from importlib.metadata import PackageNotFoundError, version

            for dist_name in ("tomato-clock-pyqt6", "tomato_clock_pyqt6"):
                try:
                    v = version(dist_name)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
                except PackageNotFoundError:
                    continue
        except Exception:
            pass
        return "0.0.0"

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
