from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QHBoxLayout, QInputDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from src.core.settings_store import SettingsStore
from src.ui.ui_theme import ACCENT, ACCENT_HOVER, BG, BORDER, MUTED, TEXT, apply_fixed_policy, apply_panel_policy, rgba
from src.ui.toggle_switch import ToggleSwitch


class _PromptRow(QWidget):
    selected = pyqtSignal(str)
    deleted = pyqtSignal(str)
    edited = pyqtSignal(str)

    def __init__(self, prompt: str, *, locked: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("PromptRow")
        self.prompt = str(prompt)
        self.locked = bool(locked)
        apply_fixed_policy(self, 44)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._selected = False
        self._random_enabled = False
        self._hovered = False
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(10)
        self.radio = QWidget(self)
        self.radio.setFixedSize(18, 18)
        self.radio.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.radio.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        radio_layout = QVBoxLayout(self.radio)
        radio_layout.setContentsMargins(0, 0, 0, 0)
        radio_layout.setSpacing(0)
        self.radio_dot = QWidget(self.radio)
        self.radio_dot.setFixedSize(8, 8)
        self.radio_dot.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        radio_layout.addWidget(self.radio_dot, 0, Qt.AlignmentFlag.AlignCenter)
        self.text_label = QLabel(self.prompt, self)
        self.text_label.setWordWrap(True)
        self.text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.text_label.setStyleSheet(f"color: {TEXT}; font-size: 14px; background: transparent;")
        self.edit_btn = QPushButton("✎", self)
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setFixedSize(24, 24)
        self.edit_btn.setStyleSheet(
            f"QPushButton {{ border: 0; background: transparent; color: {MUTED}; border-radius: 12px; font-size: 13px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {rgba(ACCENT, 0.08)}; color: {ACCENT}; }}"
        )
        self.edit_btn.clicked.connect(lambda: self.edited.emit(self.prompt))
        self.delete_btn = QPushButton("×", self)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setVisible(not self.locked)
        self.delete_btn.setStyleSheet(
            f"QPushButton {{ border: 0; background: transparent; color: {MUTED}; border-radius: 12px; font-size: 16px; }}"
            f"QPushButton:hover {{ background: {rgba(ACCENT, 0.08)}; color: {ACCENT}; }}"
        )
        self.delete_btn.clicked.connect(lambda: self.deleted.emit(self.prompt))
        self.delete_btn.setVisible(False)
        row.addWidget(self.radio, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self.text_label, 1, Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self.edit_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self.delete_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        self.set_selected(False, False)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.prompt)
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:
        self._hovered = True
        self._refresh_style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._refresh_style()
        super().leaveEvent(event)

    def set_selected(self, selected: bool, random_enabled: bool) -> None:
        self._selected = bool(selected)
        self._random_enabled = bool(random_enabled)
        self._refresh_style()

    def _refresh_style(self) -> None:
        active = self._selected and not self._random_enabled
        row_border = ACCENT if active else BORDER if self._hovered else "transparent"
        row_fill = rgba(ACCENT, 0.08) if active else BG
        self.setStyleSheet(
            f"QWidget#PromptRow {{ background: {row_fill}; border: 1.5px solid {row_border}; border-radius: 12px; }}"
        )
        radio_border = ACCENT if active else BORDER
        self.radio.setStyleSheet(
            f"background: white; border: 2px solid {radio_border}; border-radius: 9px;"
        )
        self.radio_dot.setStyleSheet(
            f"background: {ACCENT}; border-radius: 4px;" if active else "background: transparent; border-radius: 4px;"
        )
        self.delete_btn.setVisible((not self.locked) and self._hovered)


class _PromptGroup(QWidget):
    prompts_changed = pyqtSignal(list)
    selected_changed = pyqtSignal(str)

    def __init__(self, title: str, prompts: list[str], selected_prompt: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._prompts = list(prompts)
        self._selected_prompt = selected_prompt if selected_prompt in self._prompts else self._prompts[0]
        self._random_enabled = False
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 0, 20, 0)
        root.setSpacing(8)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel(title, self)
        self.title_label.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 550; background: transparent;")
        self.count_label = QLabel(self)
        self.count_label.setStyleSheet(f"color: {MUTED}; font-size: 12px; background: transparent;")
        header.addWidget(self.title_label, 0)
        header.addStretch(1)
        header.addWidget(self.count_label, 0)
        self.list_wrap = QWidget(self)
        self.list_layout = QVBoxLayout(self.list_wrap)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.input_row = QWidget(self)
        input_layout = QHBoxLayout(self.input_row)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        self.input = QLineEdit(self.input_row)
        self.input.setPlaceholderText("输入新的提示语…")
        self.input.setMaxLength(50)
        self.input.setStyleSheet(
            f"QLineEdit {{ background: white; border: 1px solid {BORDER}; border-radius: 10px; padding: 10px 12px; color: {TEXT}; font-size: 14px; }}"
            f"QLineEdit:focus {{ border: 1px solid {ACCENT}; }}"
        )
        self.confirm_btn = QPushButton("添加", self.input_row)
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_fixed_policy(self.confirm_btn, 40)
        self.confirm_btn.setMinimumWidth(64)
        self.confirm_btn.setMaximumWidth(88)
        self.confirm_btn.setStyleSheet(
            f"QPushButton {{ background: {ACCENT}; color: white; border: 0; border-radius: 10px; padding: 0 16px; font-size: 13px; font-weight: 550; }}"
            f"QPushButton:hover {{ background: {ACCENT_HOVER}; }}"
            f"QPushButton:disabled {{ background: {rgba(ACCENT, 0.38)}; color: rgba(255,255,255,0.88); }}"
        )
        self.confirm_btn.clicked.connect(self._add_prompt)
        self.input.returnPressed.connect(self._add_prompt)
        self.input.textChanged.connect(self._update_input_state)
        input_layout.addWidget(self.input, 1)
        input_layout.addWidget(self.confirm_btn, 0)
        self.input_row.hide()
        self.add_btn = QPushButton("添加提示语", self)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {MUTED}; border: 1px dashed {BORDER}; border-radius: 10px; padding: 10px; font-size: 13px; font-weight: 500; }}"
            f"QPushButton:hover {{ color: {ACCENT}; border-color: {ACCENT}; background: {rgba(ACCENT, 0.05)}; }}"
        )
        self.add_btn.clicked.connect(self._toggle_input)
        root.addLayout(header)
        root.addWidget(self.list_wrap)
        root.addWidget(self.input_row)
        root.addWidget(self.add_btn)
        self._rebuild()

    def set_random_enabled(self, enabled: bool) -> None:
        self._random_enabled = bool(enabled)
        self._rebuild()

    def sync_state(self, prompts: list[str], selected_prompt: str, random_enabled: bool) -> None:
        self._prompts = list(prompts)
        self._selected_prompt = selected_prompt if selected_prompt in self._prompts else self._prompts[0]
        self._random_enabled = bool(random_enabled)
        self._rebuild()

    def _toggle_input(self) -> None:
        if len(self._prompts) >= 10:
            return
        visible = not self.input_row.isVisible()
        self.input_row.setVisible(visible)
        if visible:
            self.input.clear()
            self.input.setFocus()
        self._update_input_state()

    def _add_prompt(self) -> None:
        prompt = self.input.text().strip()
        if not prompt or len(self._prompts) >= 10 or prompt in self._prompts:
            return
        self._prompts.append(prompt)
        self._selected_prompt = self._selected_prompt or prompt
        self.input.clear()
        self.input_row.hide()
        self._rebuild()
        self.prompts_changed.emit(list(self._prompts))
        self._update_input_state()

    def _delete_prompt(self, prompt: str) -> None:
        if len(self._prompts) <= 1:
            return
        selected_changed = self._selected_prompt == prompt
        self._prompts = [item for item in self._prompts if item != prompt]
        if self._selected_prompt not in self._prompts:
            self._selected_prompt = self._prompts[0]
        self._rebuild()
        self.prompts_changed.emit(list(self._prompts))
        if selected_changed:
            self.selected_changed.emit(self._selected_prompt)

    def _select_prompt(self, prompt: str) -> None:
        if self._random_enabled or prompt not in self._prompts:
            return
        self._selected_prompt = prompt
        self._rebuild()
        self.selected_changed.emit(prompt)

    def _edit_prompt(self, prompt: str) -> None:
        if prompt not in self._prompts:
            return
        index = self._prompts.index(prompt)
        value, accepted = QInputDialog.getText(self, "编辑提示语", "提示语", text=prompt)
        text = str(value).strip()
        if not accepted or not text:
            return
        if text != prompt and text in self._prompts:
            return
        self._prompts[index] = text
        selected_changed = self._selected_prompt == prompt
        if selected_changed:
            self._selected_prompt = text
        self._rebuild()
        self.prompts_changed.emit(list(self._prompts))
        if selected_changed:
            self.selected_changed.emit(text)

    def _rebuild(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        for index, prompt in enumerate(self._prompts):
            row = _PromptRow(prompt, locked=index == 0, parent=self.list_wrap)
            row.selected.connect(self._select_prompt)
            row.deleted.connect(self._delete_prompt)
            row.edited.connect(self._edit_prompt)
            row.set_selected(prompt == self._selected_prompt, self._random_enabled)
            self.list_layout.addWidget(row)
        self.count_label.setText(f"{len(self._prompts)} / 10")
        self.add_btn.setEnabled(len(self._prompts) < 10)
        self._update_input_state()

    def _update_input_state(self) -> None:
        prompt = self.input.text().strip()
        enabled = bool(prompt) and prompt not in self._prompts and len(self._prompts) < 10 and self.input_row.isVisible()
        self.confirm_btn.setEnabled(enabled)


class PromptSettingsPanel(QWidget):
    def __init__(self, settings: SettingsStore, parent=None):
        super().__init__(parent)
        self._settings = settings
        self.setObjectName("PromptSettingsPanel")
        apply_panel_policy(self)
        self.setStyleSheet("QWidget#PromptSettingsPanel { background: white; border: 1px solid rgba(0,0,0,0.06); border-radius: 18px; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 16)
        root.setSpacing(12)
        header = QLabel("提示语", self)
        apply_fixed_policy(header, 40)
        header.setContentsMargins(20, 16, 20, 0)
        header.setStyleSheet(f"color: {MUTED}; font-size: 13px; font-weight: 600; background: transparent;")
        switch_row = QWidget(self)
        apply_fixed_policy(switch_row, 72)
        switch_row.setObjectName("PromptSwitchRow")
        switch_row.setStyleSheet("QWidget#PromptSwitchRow { background: transparent; border-top: 1px solid rgba(0,0,0,0.06); }")
        switch_layout = QHBoxLayout(switch_row)
        switch_layout.setContentsMargins(20, 14, 20, 14)
        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel("随机显示", switch_row)
        title_label.setStyleSheet(f"color: {TEXT}; font-size: 15px; font-weight: 500; background: transparent;")
        info.addWidget(title_label)
        subtitle = QLabel("开启后随机选取一条提示语", switch_row)
        subtitle.setStyleSheet(f"color: {MUTED}; font-size: 12px; background: transparent;")
        info.addWidget(subtitle)
        info_wrap = QWidget(switch_row)
        info_wrap.setLayout(info)
        self.random_switch = ToggleSwitch(self._settings.prompt_random_enabled(), switch_row)
        self.random_switch.toggled.connect(self._on_random_changed)
        switch_layout.addWidget(info_wrap, 1)
        switch_layout.addWidget(self.random_switch, 0)
        self.focus_group = _PromptGroup(
            "专注结束提示语",
            self._settings.focus_end_prompts(),
            self._settings.selected_focus_end_prompt(),
            self,
        )
        self.rest_group = _PromptGroup(
            "休息结束提示语",
            self._settings.rest_end_prompts(),
            self._settings.selected_rest_end_prompt(),
            self,
        )
        self.focus_group.prompts_changed.connect(self._settings.set_focus_end_prompts)
        self.rest_group.prompts_changed.connect(self._settings.set_rest_end_prompts)
        self.focus_group.selected_changed.connect(self._settings.set_selected_focus_end_prompt)
        self.rest_group.selected_changed.connect(self._settings.set_selected_rest_end_prompt)
        divider = QWidget(self)
        apply_fixed_policy(divider, 1)
        divider.setStyleSheet(f"background: {rgba(BORDER, 0.65)}; margin: 0 20px;")
        root.addWidget(header)
        root.addWidget(switch_row)
        root.addWidget(self.focus_group)
        root.addWidget(divider)
        root.addWidget(self.rest_group)
        self._sync_groups()

    def _on_random_changed(self, checked: bool) -> None:
        self._settings.set_prompt_random_enabled(bool(checked))
        self._sync_groups()

    def _sync_groups(self) -> None:
        enabled = self.random_switch.isChecked()
        self.focus_group.sync_state(self._settings.focus_end_prompts(), self._settings.selected_focus_end_prompt(), enabled)
        self.rest_group.sync_state(self._settings.rest_end_prompts(), self._settings.selected_rest_end_prompt(), enabled)
