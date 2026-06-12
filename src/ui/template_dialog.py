from __future__ import annotations

from uuid import uuid4

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget

from src.core.settings_models import FocusTemplate
from src.ui.ui_theme import ACCENT, BG, BORDER, MUTED, TEXT, apply_fixed_policy, rgba


def _is_emoji_symbol(text: str) -> bool:
    value = str(text).strip()
    if not value:
        return False
    if any(ch.isalnum() or ch.isspace() for ch in value):
        return False
    return any(ord(ch) >= 0x2600 for ch in value)


class TemplateDialog(QDialog):
    def __init__(self, template: FocusTemplate | None = None, parent=None):
        super().__init__(parent)
        self._original = template
        self._template: FocusTemplate | None = None
        editing = template is not None
        self.setWindowTitle("编辑模板" if editing else "添加模板")
        self.setModal(True)
        self.setFixedWidth(420)
        self.setStyleSheet(f"QDialog {{ background: white; }} QWidget {{ color: {TEXT}; }}")
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(16)
        title = QLabel("编辑模板" if editing else "添加模板", self)
        title.setStyleSheet(f"font-size: 18px; font-weight: 600;")
        root.addWidget(title)
        self.name_edit = self._text_field("模板名称", "例如：晨间专注", root)
        emoji_row = QWidget(self)
        emoji_layout = QHBoxLayout(emoji_row)
        emoji_layout.setContentsMargins(0, 0, 0, 0)
        emoji_layout.setSpacing(10)
        self.emoji_preview = QLabel("🍅", emoji_row)
        self.emoji_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.emoji_preview.setFixedSize(44, 44)
        self.emoji_preview.setStyleSheet(f"background: {BG}; border: 1px solid {BORDER}; border-radius: 12px; font-size: 24px;")
        emoji_layout.addWidget(self.emoji_preview, 0)
        self.emoji_edit = QLineEdit(emoji_row)
        self.emoji_edit.setPlaceholderText("输入 emoji 符号")
        self.emoji_edit.textChanged.connect(self._sync_emoji_preview)
        self._style_input(self.emoji_edit)
        emoji_layout.addWidget(self.emoji_edit, 1)
        root.addWidget(self._field_wrap("Emoji 符号", emoji_row))
        duration_row = QWidget(self)
        duration_layout = QHBoxLayout(duration_row)
        duration_layout.setContentsMargins(0, 0, 0, 0)
        duration_layout.setSpacing(10)
        self.focus_spin = self._spin_box(1, 180, 25)
        self.short_spin = self._spin_box(1, 60, 5)
        self.long_spin = self._spin_box(1, 90, 15)
        duration_layout.addWidget(self._mini_field("专注(分钟)", self.focus_spin), 1)
        duration_layout.addWidget(self._mini_field("短休息(分钟)", self.short_spin), 1)
        duration_layout.addWidget(self._mini_field("长休息(分钟)", self.long_spin), 1)
        root.addWidget(self._field_wrap("时长设置", duration_row))
        self.rounds_spin = self._spin_box(1, 12, 4)
        root.addWidget(self._field_wrap("次数", self._mini_field("每 N 次专注后", self.rounds_spin)))
        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel_btn = QPushButton("取消", self)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background: {BG}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 10px; padding: 10px 22px; font-size: 14px; font-weight: 600; }}"
        )
        confirm_btn = QPushButton("保存" if editing else "添加", self)
        confirm_btn.clicked.connect(self._submit)
        confirm_btn.setStyleSheet(
            f"QPushButton {{ background: {ACCENT}; color: white; border: 0; border-radius: 10px; padding: 10px 22px; font-size: 14px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {rgba(ACCENT, 0.9)}; }}"
        )
        actions.addWidget(cancel_btn, 0)
        actions.addWidget(confirm_btn, 0)
        root.addLayout(actions)
        if template is not None:
            self.name_edit.setText(template.name)
            self.emoji_edit.setText(template.emoji)
            self.focus_spin.setValue(template.focus_minutes)
            self.short_spin.setValue(template.short_break_minutes)
            self.long_spin.setValue(template.long_break_minutes)
            self.rounds_spin.setValue(template.rounds)
            self._sync_emoji_preview(template.emoji)

    def template(self) -> FocusTemplate | None:
        return self._template

    def _text_field(self, label: str, placeholder: str, root: QVBoxLayout) -> QLineEdit:
        edit = QLineEdit(self)
        edit.setPlaceholderText(placeholder)
        self._style_input(edit)
        root.addWidget(self._field_wrap(label, edit))
        return edit

    def _field_wrap(self, label: str, widget: QWidget) -> QWidget:
        wrap = QWidget(self)
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        title = QLabel(label, wrap)
        title.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 550;")
        layout.addWidget(title)
        layout.addWidget(widget)
        return wrap

    def _mini_field(self, label: str, widget: QWidget) -> QWidget:
        wrap = QWidget(self)
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(widget)
        hint = QLabel(label, wrap)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        layout.addWidget(hint)
        return wrap

    def _spin_box(self, minimum: int, maximum: int, value: int) -> QSpinBox:
        spin = QSpinBox(self)
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        apply_fixed_policy(spin, 40)
        spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        spin.setStyleSheet(
            f"QSpinBox {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 10px; padding: 0 12px; font-size: 14px; font-weight: 600; }}"
            f"QSpinBox:focus {{ border: 1px solid {ACCENT}; }}"
        )
        return spin

    def _style_input(self, widget: QLineEdit) -> None:
        apply_fixed_policy(widget, 40)
        widget.setStyleSheet(
            f"QLineEdit {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 10px; padding: 0 14px; font-size: 14px; }}"
            f"QLineEdit:focus {{ border: 1px solid {ACCENT}; }}"
        )

    def _sync_emoji_preview(self, text: str) -> None:
        self.emoji_preview.setText(text.strip() or "🍅")

    def _submit(self) -> None:
        name = self.name_edit.text().strip()
        emoji = self.emoji_edit.text().strip() or "🍅"
        if not name:
            self.name_edit.setFocus()
            return
        if not _is_emoji_symbol(emoji):
            self.emoji_edit.setFocus()
            return
        self._template = FocusTemplate(
            id=self._original.id if self._original is not None else uuid4().hex,
            name=name,
            emoji=emoji,
            focus_minutes=self.focus_spin.value(),
            short_break_minutes=self.short_spin.value(),
            long_break_minutes=self.long_spin.value(),
            rounds=self.rounds_spin.value(),
        )
        self.accept()
