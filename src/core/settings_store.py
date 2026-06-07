from __future__ import annotations

import json
from typing import Iterable

from PyQt6.QtCore import QSettings


class SettingsStore:
    def __init__(self):
        self._settings = QSettings("tomato-clock", "tomato-clock-pyqt6")
        self._default_focus_types = ["学习", "阅读", "健身", "工作"]
        self._default_focus_colors = {
            "学习": "#4F46E5",
            "阅读": "#10B981",
            "健身": "#F97316",
            "工作": "#0EA5E9",
        }

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
        if isinstance(value, list) and all(isinstance(x, str) for x in value):
            return value
        if isinstance(value, str) and value:
            return [value]
        return list(self._default_focus_types)

    def set_focus_types(self, types: Iterable[str]) -> None:
        cleaned = [t.strip() for t in types if isinstance(t, str) and t.strip()]
        if not cleaned:
            cleaned = list(self._default_focus_types)
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
                    return result
            except Exception:
                pass
        return dict(self._default_focus_colors)

    def set_focus_type_color(self, focus_type: str, color_hex: str) -> None:
        colors = self.focus_type_colors()
        colors[str(focus_type)] = str(color_hex)
        self._settings.setValue("focus/type_colors", json.dumps(colors, ensure_ascii=False))

    def set_default_focus_type(self, focus_type: str) -> None:
        self._settings.setValue("focus/default_type", str(focus_type))
