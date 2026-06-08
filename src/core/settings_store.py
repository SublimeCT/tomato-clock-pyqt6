from __future__ import annotations

import json
from typing import Iterable

from PyQt6.QtCore import QSettings


class SettingsStore:
    def __init__(self):
        self._settings = QSettings("tomato-clock", "tomato-clock-pyqt6")
        self._default_focus_types = ["学习", "阅读", "健身", "工作", "专注", "冥想", "烹饪", "瑜伽"]
        self._default_focus_colors = {
            "学习": "#4F46E5",
            "阅读": "#10B981",
            "健身": "#F97316",
            "工作": "#0EA5E9",
            "专注": "#7C3AED",
            "冥想": "#14B8A6",
            "烹饪": "#F59E0B",
            "瑜伽": "#EC4899",
        }

    def builtin_focus_types(self) -> list[str]:
        return list(self._default_focus_types)

    def is_builtin_focus_type(self, focus_type: str) -> bool:
        return str(focus_type) in set(self._default_focus_types)

    def add_focus_type(self, name: str, *, default_color_hex: str = "#4F46E5") -> bool:
        name = str(name).strip()
        if not name:
            return False
        if self.is_builtin_focus_type(name):
            return False
        types = self.focus_types()
        if name in types:
            return False
        types.append(name)
        self.set_focus_types(types)
        self.set_focus_type_color(name, str(default_color_hex))
        return True

    def rename_focus_type(self, old: str, new: str) -> bool:
        old = str(old).strip()
        new = str(new).strip()
        if not old or not new:
            return False
        if self.is_builtin_focus_type(old):
            return False
        if self.is_builtin_focus_type(new):
            return False
        types = self.focus_types()
        if old not in types:
            return False
        if new in types and new != old:
            return False

        updated: list[str] = []
        for t in types:
            updated.append(new if t == old else t)
        self.set_focus_types(updated)

        colors = self.focus_type_colors()
        if old in colors:
            colors[new] = colors.get(old, "#4F46E5")
            colors.pop(old, None)
            self._save_focus_type_colors(colors)

        if self.default_focus_type() == old:
            self.set_default_focus_type(new)
        return True

    def delete_focus_type(self, focus_type: str) -> bool:
        focus_type = str(focus_type).strip()
        if not focus_type:
            return False
        if self.is_builtin_focus_type(focus_type):
            return False

        types = self.focus_types()
        if focus_type not in types:
            return False

        updated = [t for t in types if t != focus_type]
        self.set_focus_types(updated)
        if self.default_focus_type() == focus_type:
            self.set_default_focus_type(self.focus_types()[0])
        return True

    def focus_minutes(self) -> int:
        return int(self._settings.value("durations/focus_minutes", 25))

    def set_focus_minutes(self, minutes: int) -> None:
        self._settings.setValue("durations/focus_minutes", int(minutes))

    def short_break_minutes(self) -> int:
        return int(self._settings.value("durations/short_break_minutes", 5))

    def set_short_break_minutes(self, minutes: int) -> None:
        self._settings.setValue("durations/short_break_minutes", int(minutes))

    def long_break_minutes(self) -> int:
        return int(self._settings.value("durations/long_break_minutes", 15))

    def set_long_break_minutes(self, minutes: int) -> None:
        self._settings.setValue("durations/long_break_minutes", int(minutes))

    def long_break_every(self) -> int:
        return int(self._settings.value("durations/long_break_every", 4))

    def set_long_break_every(self, count: int) -> None:
        self._settings.setValue("durations/long_break_every", int(count))

    def focus_types(self) -> list[str]:
        value = self._settings.value("focus/types", None)
        stored: list[str] = []
        if isinstance(value, list) and all(isinstance(x, str) for x in value):
            stored = [x.strip() for x in value if x.strip()]
        elif isinstance(value, str) and value.strip():
            stored = [value.strip()]

        builtin = list(self._default_focus_types)
        custom = [t for t in stored if t not in set(builtin)]
        unique_custom: list[str] = []
        seen = set()
        for t in custom:
            if t not in seen:
                unique_custom.append(t)
                seen.add(t)
        return builtin + unique_custom

    def set_focus_types(self, types: Iterable[str]) -> None:
        cleaned = [t.strip() for t in types if isinstance(t, str) and t.strip()]
        cleaned = [t for t in cleaned if t not in set(self._default_focus_types)]
        unique_custom: list[str] = []
        seen = set()
        for t in cleaned:
            if t not in seen:
                unique_custom.append(t)
                seen.add(t)
        cleaned = list(self._default_focus_types) + unique_custom
        self._settings.setValue("focus/types", cleaned)
        colors = self.focus_type_colors()
        self._settings.setValue(
            "focus/type_colors",
            json.dumps({k: v for k, v in colors.items() if k in set(cleaned)}, ensure_ascii=False),
        )

    def default_focus_type(self) -> str:
        value = self._settings.value("focus/default_type", None)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return self.focus_types()[0]

    def focus_type_colors(self) -> dict[str, str]:
        raw = self._settings.value("focus/type_colors", None)
        if isinstance(raw, str) and raw.strip():
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    result: dict[str, str] = {}
                    for k, v in data.items():
                        if isinstance(k, str) and isinstance(v, str) and v.startswith("#"):
                            result[k] = v
                    for k, v in self._default_focus_colors.items():
                        if k not in result:
                            result[k] = v
                    return result
            except Exception:
                pass
        return dict(self._default_focus_colors)

    def _save_focus_type_colors(self, colors: dict[str, str]) -> None:
        self._settings.setValue("focus/type_colors", json.dumps(colors, ensure_ascii=False))

    def set_focus_type_color(self, focus_type: str, color_hex: str) -> None:
        if self.is_builtin_focus_type(focus_type):
            return
        colors = self.focus_type_colors()
        colors[str(focus_type)] = str(color_hex)
        self._save_focus_type_colors(colors)

    def set_default_focus_type(self, focus_type: str) -> None:
        self._settings.setValue("focus/default_type", str(focus_type))
