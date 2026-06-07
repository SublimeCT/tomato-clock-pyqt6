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
)

from src.core.settings_store import SettingsStore
from src.ui.focus_type_cards import FocusTypeCard


class FocusTypeDialog(QDialog):
    def __init__(self, settings: SettingsStore, current_type: str):
        super().__init__()
        self._settings = settings
        self._selected = current_type

        self.setWindowTitle("选择专注类型")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(520, 520)
        self.setStyleSheet(
            "QDialog { background: #f6f7fb; }"
            "QScrollArea { background: transparent; }"
            "QLabel { color: rgba(0,0,0,0.82); }"
            "QPushButton { padding: 10px 14px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.10); background: rgba(255,255,255,0.92); }"
            "QPushButton:hover { background: rgba(255,255,255,1.0); }"
            "QPushButton:pressed { background: rgba(245,245,245,1.0); }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("专注类型", self)
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        subtitle = QLabel("点击卡片选择类型；可修改颜色；删除需二次确认。", self)
        subtitle.setStyleSheet("color: rgba(0,0,0,0.55);")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(subtitle)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget(self)
        self.grid = QGridLayout(content)
        self.grid.setContentsMargins(6, 6, 6, 6)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)
        self.scroll_area.setWidget(content)

        footer = QHBoxLayout()
        self.cancel_btn = QPushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        footer.addStretch(1)
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

        cards: list[FocusTypeCard] = []
        for t in types:
            cards.append(
                FocusTypeCard(
                    focus_type=t,
                    color_hex=colors.get(t, "#4F46E5"),
                    on_select=self._select_and_close,
                    on_delete=self._delete_type,
                    on_color=self._pick_color,
                )
            )

        cards.append(
            FocusTypeCard(
                focus_type="新建",
                color_hex="#111827",
                on_select=self._create_type,
                on_delete=None,
                on_color=None,
                is_new=True,
            )
        )

        col_count = 2
        for i, card in enumerate(cards):
            row = i // col_count
            col = i % col_count
            self.grid.addWidget(card, row, col)

    def _select_and_close(self, focus_type: str) -> None:
        self._selected = focus_type
        self._settings.set_default_focus_type(focus_type)
        self.accept()

    def _create_type(self, _unused: str) -> None:
        text, ok = QInputDialog.getText(self, "新建专注类型", "名称：")
        if not ok:
            return
        name = text.strip()
        if not name:
            return

        types = self._settings.focus_types()
        if name in types:
            QMessageBox.information(self, "已存在", "该专注类型已存在。")
            return

        types.append(name)
        self._settings.set_focus_types(types)
        self._settings.set_focus_type_color(name, "#4F46E5")
        self._selected = name
        self._settings.set_default_focus_type(name)
        self._reload_cards()

    def _delete_type(self, focus_type: str) -> None:
        types = self._settings.focus_types()
        if len(types) <= 1:
            QMessageBox.information(self, "无法删除", "至少保留一个专注类型。")
            return
        if (
            QMessageBox.question(self, "删除专注类型", f"确定删除「{focus_type}」？")
            != QMessageBox.StandardButton.Yes
        ):
            return

        updated = [t for t in types if t != focus_type]
        self._settings.set_focus_types(updated)
        if self._selected == focus_type:
            self._selected = updated[0]
            self._settings.set_default_focus_type(updated[0])
        self._reload_cards()

    def _pick_color(self, focus_type: str) -> None:
        colors = self._settings.focus_type_colors()
        current = QColor(colors.get(focus_type, "#4F46E5"))
        picked = QColorDialog.getColor(current, self, "选择颜色")
        if not picked.isValid():
            return
        self._settings.set_focus_type_color(focus_type, picked.name())
        self._reload_cards()
