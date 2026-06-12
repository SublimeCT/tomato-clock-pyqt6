from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QAbstractScrollArea, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from src.core.settings_models import FocusTemplate
from src.core.settings_store import SettingsStore
from src.ui.template_dialog import TemplateDialog
from src.ui.ui_theme import BG, BORDER, MUTED, TEXT, apply_fixed_policy, apply_panel_policy, rgba


class _TemplateCard(QWidget):
    delete_requested = pyqtSignal(str)
    edit_requested = pyqtSignal(str)

    def __init__(self, template: FocusTemplate, *, builtin: bool, parent=None):
        super().__init__(parent)
        self.template = template
        self.setObjectName("TemplateCard")
        apply_panel_policy(self, 92)
        self.setStyleSheet("QWidget#TemplateCard { background: white; border: 1px solid rgba(0,0,0,0.06); border-radius: 18px; }")
        row = QHBoxLayout(self)
        row.setContentsMargins(18, 16, 18, 16)
        row.setSpacing(14)
        emoji = QLabel(template.emoji, self)
        emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji.setFixedSize(44, 44)
        emoji.setStyleSheet(f"background: {BG}; border-radius: 12px; font-size: 24px;")
        info_wrap = QWidget(self)
        info = QVBoxLayout(info_wrap)
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(4)
        name = QLabel(template.name, info_wrap)
        name.setStyleSheet(f"color: {TEXT}; font-size: 15px; font-weight: 600;")
        meta = QLabel(
            f"专注 {template.focus_minutes} 分钟  ·  短休 {template.short_break_minutes}  ·  长休 {template.long_break_minutes}  ·  {template.rounds} 次",
            info_wrap,
        )
        meta.setWordWrap(True)
        meta.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
        info.addWidget(name)
        info.addWidget(meta)
        actions = QVBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(6)
        edit_btn = QPushButton("✎", self)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setFixedSize(32, 32)
        edit_btn.setStyleSheet(
            f"QPushButton {{ border: 0; background: transparent; color: {MUTED}; border-radius: 8px; font-size: 14px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {rgba('#E63946', 0.08)}; color: #E63946; }}"
        )
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(template.id))
        delete_btn = QPushButton("×", self)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setFixedSize(32, 32)
        delete_btn.setVisible(not builtin)
        delete_btn.setStyleSheet(
            f"QPushButton {{ border: 0; background: transparent; color: {MUTED}; border-radius: 16px; font-size: 16px; }}"
            f"QPushButton:hover {{ background: {rgba('#E63946', 0.08)}; color: #E63946; }}"
        )
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(template.id))
        row.addWidget(emoji, 0, Qt.AlignmentFlag.AlignTop)
        row.addWidget(info_wrap, 1)
        actions.addWidget(edit_btn, 0, Qt.AlignmentFlag.AlignRight)
        actions.addWidget(delete_btn, 0, Qt.AlignmentFlag.AlignRight)
        actions.addStretch(1)
        actions_wrap = QWidget(self)
        actions_wrap.setLayout(actions)
        row.addWidget(actions_wrap, 0, Qt.AlignmentFlag.AlignTop)


class TemplatePage(QWidget):
    templates_changed = pyqtSignal()

    def __init__(self, settings: SettingsStore, parent=None):
        super().__init__(parent)
        self._settings = settings
        self.setStyleSheet("TemplatePage { background: #FDF6F0; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 24)
        root.setSpacing(0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QAbstractScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget(scroll)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 24, 24, 0)
        body_layout.setSpacing(12)
        title = QLabel("专注模板", body)
        title.setStyleSheet(f"color: {TEXT}; font-size: 22px; font-weight: 700;")
        desc = QLabel("创建不同的专注模板，快速切换工作节奏", body)
        desc.setStyleSheet(f"color: {MUTED}; font-size: 14px;")
        self.list_wrap = QWidget(body)
        self.list_layout = QVBoxLayout(self.list_wrap)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)
        self.add_btn = QPushButton("添加模板", body)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {MUTED}; border: 1px dashed {BORDER}; border-radius: 18px; padding: 14px; font-size: 14px; font-weight: 500; }}"
            f"QPushButton:hover {{ color: #E63946; border-color: #E63946; background: {rgba('#E63946', 0.05)}; }}"
        )
        self.add_btn.clicked.connect(self._open_add_dialog)
        body_layout.addWidget(title)
        body_layout.addWidget(desc)
        body_layout.addWidget(self.list_wrap)
        body_layout.addWidget(self.add_btn)
        body_layout.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)
        self.reload_templates()

    def reload_templates(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        templates = self._settings.templates()
        if not templates:
            empty = QLabel("还没有模板，先添加一个吧", self.list_wrap)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            apply_fixed_policy(empty, 84)
            empty.setStyleSheet(
                f"background: white; color: {MUTED}; border: 1px dashed {BORDER}; border-radius: 18px; font-size: 13px;"
            )
            self.list_layout.addWidget(empty)
            return
        for template in templates:
            card = _TemplateCard(template, builtin=self._settings.is_builtin_template(template.id), parent=self.list_wrap)
            card.delete_requested.connect(self._delete_template)
            card.edit_requested.connect(self._edit_template)
            self.list_layout.addWidget(card)

    def _open_add_dialog(self) -> None:
        dialog = TemplateDialog(parent=self)
        if dialog.exec() != TemplateDialog.DialogCode.Accepted:
            return
        template = dialog.template()
        if template is None:
            return
        if self._settings.add_template(template):
            self.reload_templates()
            self.templates_changed.emit()

    def _edit_template(self, template_id: str) -> None:
        template = self._settings.template_by_id(template_id)
        if template is None:
            return
        dialog = TemplateDialog(template, parent=self)
        if dialog.exec() != TemplateDialog.DialogCode.Accepted:
            return
        updated = dialog.template()
        if updated is None:
            return
        if self._settings.update_template(updated):
            self.reload_templates()
            self.templates_changed.emit()

    def _delete_template(self, template_id: str) -> None:
        if self._settings.delete_template(template_id):
            self.reload_templates()
            self.templates_changed.emit()
