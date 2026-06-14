from __future__ import annotations

from dataclasses import dataclass

from src.core.pomodoro_engine import EngineState
from src.core.settings_store import SettingsStore
from src.ui.ui_theme import SUCCESS


@dataclass(frozen=True)
class TrayPopupState:
    label: str
    color_hex: str
    progress: float


def build_tray_popup_state(
    settings: SettingsStore,
    state: EngineState,
    focus_type_colors: dict[str, str],
) -> TrayPopupState:
    total = max(1, int(state.total_seconds))
    progress = max(0.0, min(1.0, 1.0 - (float(state.remaining_seconds) / float(total))))
    focus_color = focus_type_colors.get(state.focus_type, "#4F46E5")
    template = settings.template_by_id(state.template_id)
    if state.phase == "focus":
        if template is not None:
            return TrayPopupState(f"{template.emoji} {template.name}".strip(), focus_color, progress)
        return TrayPopupState(str(state.focus_type), focus_color, progress)
    rest_icon = "☕" if state.phase == "short_break" else "🌙"
    if template is not None:
        return TrayPopupState(f"{rest_icon} {template.emoji} {template.name}".strip(), SUCCESS, progress)
    rest_name = "短休息" if state.phase == "short_break" else "长休息"
    return TrayPopupState(f"{rest_icon} {rest_name}", SUCCESS, progress)
