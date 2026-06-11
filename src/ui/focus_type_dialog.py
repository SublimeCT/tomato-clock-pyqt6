from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QColorDialog,
    QInputDialog,
    QSizePolicy,
)

from src.core.settings_store import SettingsStore
from src.ui.focus_type_cards import FocusTypeCard
from src.ui.ui_theme import ACCENT, BG, BORDER, MUTED, TEXT, apply_fixed_policy, rgba


class FocusTypeDialog(QDialog):
    def __init__(self, settings: SettingsStore, current_type: str):
        super().__init__()
        self._settings = settings
        self._selected = current_type
        self._builtin_types = set(self._settings.builtin_focus_types())
        self._cards: dict[str, FocusTypeCard] = {}

        self.setWindowTitle("选择专注类型")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(600, 560)
        self.setStyleSheet(
            f"QDialog {{ background: {BG}; }}"
            "QScrollArea { background: transparent; }"
            "QScrollArea QWidget { background: transparent; }"
            f"QLabel {{ color: {TEXT}; }}"
            f"QPushButton {{ padding: 6px 12px; border-radius: 10px; border: 1px solid {BORDER}; background: white; }}"
            f"QPushButton:hover {{ background: {rgba(ACCENT, 0.08)}; }}"
            f"QPushButton:pressed {{ background: {rgba(ACCENT, 0.14)}; }}"
            f"QPushButton#AddBtn {{ border: 1px solid {ACCENT}; background: {ACCENT}; color: white; font-weight: 700; }}"
            f"QPushButton#AddBtn:hover {{ background: #D62828; }}"
            f"QPushButton#OkBtn {{ border: 1px solid {ACCENT}; background: {ACCENT}; color: white; font-weight: 700; }}"
            f"QPushButton#OkBtn:hover {{ background: #D62828; }}"
            f"QPushButton#CancelBtn {{ border: 1px solid {BORDER}; background: white; color: {TEXT}; font-weight: 650; }}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(10)
        title = QLabel("专注类型", self)
        apply_fixed_policy(title, 28)
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT};")
        subtitle = QLabel("默认类型不可编辑；自定义类型支持添加/重命名/删除。", self)
        apply_fixed_policy(subtitle, 24)
        subtitle.setStyleSheet(f"color: {MUTED};")

        add_btn = QPushButton("添加", self)
        add_btn.setObjectName("AddBtn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._create_type)

        header.addWidget(title)
        header.addWidget(subtitle, 1)
        header.addWidget(add_btn)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget(self)
        content.setObjectName("FocusTypeDialogContent")
        self.grid = QGridLayout(content)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
        self.scroll_area.setWidget(content)

        footer = QHBoxLayout()
        self.ok_btn = QPushButton("确定", self)
        self.ok_btn.setObjectName("OkBtn")
        self.ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ok_btn.clicked.connect(self._confirm)
        self.cancel_btn = QPushButton("取消", self)
        self.cancel_btn.setObjectName("CancelBtn")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)

        btns = [add_btn, self.ok_btn, self.cancel_btn]
        fm = add_btn.fontMetrics()
        texts = [b.text() for b in btns]
        min_width = max(112, *(fm.horizontalAdvance(t) + 12 * 2 + 22 for t in texts))
        for b in btns:
            b.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            b.setMinimumWidth(min_width)
            b.setFixedHeight(42)
        footer.addStretch(1)
        footer.addWidget(self.ok_btn)
        footer.addWidget(self.cancel_btn)

        root.addLayout(header)
        root.addWidget(self.scroll_area, 1)
        root.addLayout(footer)

        self._reload_cards()

    def selected_type(self) -> str:
        return self._selected

    def _reload_cards(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.deleteLater()

        types = self._settings.focus_types()
        colors = self._settings.focus_type_colors()

        self._cards = {}
        cards: list[FocusTypeCard] = []
        for t in types:
            locked = t in self._builtin_types
            card = (
                FocusTypeCard(
                    focus_type=t,
                    color_hex=colors.get(t, "#4F46E5"),
                    on_select=self._select_only,
                    on_delete=None if locked else self._delete_type,
                    on_color=None if locked else self._pick_color,
                    on_edit=None if locked else self._edit_type,
                    selected=(t == self._selected),
                    locked=locked,
                )
            )
            cards.append(card)
            self._cards[t] = card

        col_count = 2
        for i, card in enumerate(cards):
            row = i // col_count
            col = i % col_count
            self.grid.addWidget(card, row, col, Qt.AlignmentFlag.AlignHCenter)

    def _select_only(self, focus_type: str) -> None:
        self._selected = focus_type
        for t, c in self._cards.items():
            c.set_selected(t == focus_type)

    def _confirm(self) -> None:
        self._settings.set_default_focus_type(self._selected)
        self.accept()

    def _create_type(self) -> None:
        text, ok = QInputDialog.getText(self, "添加专注类型", "名称：")
        if not ok:
            return
        name = text.strip()
        if not name:
            return

        if name in self._settings.focus_types():
            QMessageBox.information(self, "已存在", "该专注类型已存在。")
            return
        if self._settings.is_builtin_focus_type(name):
            QMessageBox.information(self, "不可用", "该名称为默认类型保留名称。")
            return

        if not self._settings.add_focus_type(name, default_color_hex="#4F46E5"):
            QMessageBox.information(self, "添加失败", "无法添加该专注类型。")
            return
        self._selected = name
        self._settings.set_default_focus_type(name)
        self._reload_cards()

    def _edit_type(self, focus_type: str) -> None:
        if focus_type in self._builtin_types:
            QMessageBox.information(self, "无法编辑", "默认专注类型不可编辑。")
            return

        text, ok = QInputDialog.getText(self, "重命名专注类型", "新名称：", text=focus_type)
        if not ok:
            return
        name = text.strip()
        if not name:
            return
        if self._settings.is_builtin_focus_type(name):
            QMessageBox.information(self, "不可用", "该名称为默认类型保留名称。")
            return

        if name in self._settings.focus_types() and name != focus_type:
            QMessageBox.information(self, "已存在", "该专注类型已存在。")
            return

        if not self._settings.rename_focus_type(focus_type, name):
            QMessageBox.information(self, "重命名失败", "无法重命名该专注类型。")
            return
        if self._selected == focus_type:
            self._selected = name

        self._reload_cards()

    def _delete_type(self, focus_type: str) -> None:
        if focus_type in self._builtin_types:
            QMessageBox.information(self, "无法删除", "默认专注类型不可删除。")
            return
        if (
            QMessageBox.question(self, "删除专注类型", f"确定删除「{focus_type}」？")
            != QMessageBox.StandardButton.Yes
        ):
            return

        if not self._settings.delete_focus_type(focus_type):
            QMessageBox.information(self, "删除失败", "无法删除该专注类型。")
            return
        if self._selected == focus_type:
            self._selected = self._settings.default_focus_type()
        self._reload_cards()

    def _pick_color(self, focus_type: str) -> None:
        if focus_type in self._builtin_types:
            QMessageBox.information(self, "无法修改", "默认专注类型不可修改。")
            return
        colors = self._settings.focus_type_colors()
        current = QColor(colors.get(focus_type, "#4F46E5"))
        picked = QColorDialog.getColor(current, self, "选择颜色")
        if not picked.isValid():
            return
        self._settings.set_focus_type_color(focus_type, picked.name())
        self._reload_cards()
