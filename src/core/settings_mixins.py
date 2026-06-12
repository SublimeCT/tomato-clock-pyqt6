from __future__ import annotations

import json
import random
from dataclasses import asdict
from typing import Iterable

from PyQt6.QtCore import QSettings
from src.core.settings_models import (
    BUILTIN_BREAK_PROMPT_ID,
    BUILTIN_FOCUS_PROMPT_ID,
    FocusTemplate,
    builtin_template_ids,
    sanitize_prompts,
    template_from_dict,
)


class PromptSettingsMixin:
    _settings: QSettings
    _default_focus_end_prompt: str
    _default_break_end_prompt: str

    def prompt_random_enabled(self) -> bool:
        return str(self._settings.value("prompts/random_enabled", "false")).lower() == "true"

    def set_prompt_random_enabled(self, enabled: bool) -> None:
        self._settings.setValue("prompts/random_enabled", "true" if enabled else "false")

    def focus_end_prompts(self) -> list[str]:
        return self._load_prompt_bundle("prompts/focus_end", self._default_focus_end_prompt, BUILTIN_FOCUS_PROMPT_ID)[1]

    def set_focus_end_prompts(self, prompts: Iterable[str]) -> None:
        items = sanitize_prompts(prompts, self._default_focus_end_prompt)
        self._save_prompt_bundle("prompts/focus_end", items[0], items[1:], BUILTIN_FOCUS_PROMPT_ID)
        if self.selected_focus_end_prompt() not in items:
            self.set_selected_focus_end_prompt(items[0])

    def rest_end_prompts(self) -> list[str]:
        return self._load_prompt_bundle("prompts/rest_end", self._default_break_end_prompt, BUILTIN_BREAK_PROMPT_ID)[1]

    def set_rest_end_prompts(self, prompts: Iterable[str]) -> None:
        items = sanitize_prompts(prompts, self._default_break_end_prompt)
        self._save_prompt_bundle("prompts/rest_end", items[0], items[1:], BUILTIN_BREAK_PROMPT_ID)
        if self.selected_rest_end_prompt() not in items:
            self.set_selected_rest_end_prompt(items[0])

    def set_builtin_focus_end_prompt(self, prompt: str) -> None:
        builtin, prompts = self._load_prompt_bundle("prompts/focus_end", self._default_focus_end_prompt, BUILTIN_FOCUS_PROMPT_ID)
        items = list(prompts)
        previous = builtin
        builtin = sanitize_prompts([prompt], self._default_focus_end_prompt)[0]
        self._save_prompt_bundle("prompts/focus_end", builtin, items[1:], BUILTIN_FOCUS_PROMPT_ID)
        if self.selected_focus_end_prompt() == previous:
            self.set_selected_focus_end_prompt(builtin)

    def set_builtin_rest_end_prompt(self, prompt: str) -> None:
        builtin, prompts = self._load_prompt_bundle("prompts/rest_end", self._default_break_end_prompt, BUILTIN_BREAK_PROMPT_ID)
        items = list(prompts)
        previous = builtin
        builtin = sanitize_prompts([prompt], self._default_break_end_prompt)[0]
        self._save_prompt_bundle("prompts/rest_end", builtin, items[1:], BUILTIN_BREAK_PROMPT_ID)
        if self.selected_rest_end_prompt() == previous:
            self.set_selected_rest_end_prompt(builtin)

    def selected_focus_end_prompt(self) -> str:
        return self._selected_prompt("prompts/focus_selected", self.focus_end_prompts())

    def set_selected_focus_end_prompt(self, prompt: str) -> None:
        prompts = self.focus_end_prompts()
        value = str(prompt).strip()
        self._settings.setValue("prompts/focus_selected", value if value in prompts else prompts[0])

    def selected_rest_end_prompt(self) -> str:
        return self._selected_prompt("prompts/rest_selected", self.rest_end_prompts())

    def set_selected_rest_end_prompt(self, prompt: str) -> None:
        prompts = self.rest_end_prompts()
        value = str(prompt).strip()
        self._settings.setValue("prompts/rest_selected", value if value in prompts else prompts[0])

    def pick_focus_end_prompt(self) -> str:
        return self._pick_prompt(self.focus_end_prompts(), self.selected_focus_end_prompt())

    def pick_rest_end_prompt(self) -> str:
        return self._pick_prompt(self.rest_end_prompts(), self.selected_rest_end_prompt())

    def _load_prompt_bundle(self, key: str, fallback: str, builtin_id: str) -> tuple[str, list[str]]:
        data = self._load_json_value(self._settings.value(key, None))
        if isinstance(data, dict):
            builtin = sanitize_prompts([data.get("builtin", fallback)], fallback)[0]
            customs = self._sanitize_custom_prompts(data.get("customs", []), builtin)
            prompts = [builtin] + customs
            return builtin, prompts
        if isinstance(data, list):
            legacy = sanitize_prompts(data, fallback)
            builtin = legacy[0] if legacy and legacy[0] == fallback else fallback
            customs = self._sanitize_custom_prompts(legacy[1:] if legacy and legacy[0] == fallback else legacy, builtin)
            prompts = [builtin] + customs
            self._save_prompt_bundle(key, builtin, customs, builtin_id)
            return builtin, prompts
        return fallback, [fallback]

    def _sanitize_custom_prompts(self, prompts: object, builtin_prompt: str) -> list[str]:
        if not isinstance(prompts, list):
            return []
        result: list[str] = []
        seen = {builtin_prompt}
        for item in prompts:
            text = str(item).strip()
            if not text or text in seen:
                continue
            result.append(text[:50])
            seen.add(text)
            if len(result) >= 9:
                break
        return result

    def _save_prompt_bundle(self, key: str, builtin: str, customs: list[str], builtin_id: str) -> None:
        payload = {"id": builtin_id, "builtin": builtin, "customs": customs}
        self._save_json(key, payload)

    def _selected_prompt(self, key: str, prompts: list[str]) -> str:
        value = self._settings.value(key, "")
        picked = str(value).strip() if value is not None else ""
        return picked if picked in prompts else prompts[0]

    def _pick_prompt(self, prompts: list[str], selected: str) -> str:
        if self.prompt_random_enabled() and prompts:
            return random.choice(prompts)
        return selected if selected in prompts else prompts[0]

    def _save_json(self, _key: str, _payload: object) -> None:
        raise NotImplementedError

    def _load_json_value(self, _raw: object) -> object:
        raise NotImplementedError


class TemplateSettingsMixin:
    _settings: QSettings
    _default_templates: list[FocusTemplate]

    def templates(self) -> list[FocusTemplate]:
        raw = self._settings.value("templates/items", None)
        if raw is None:
            return list(self._default_templates)
        data = self._load_json_value(raw)
        if not isinstance(data, list):
            return list(self._default_templates)
        templates: list[FocusTemplate] = []
        seen_ids: set[str] = set()
        for item in data:
            template = template_from_dict(item)
            if template is None or template.id in seen_ids:
                continue
            seen_ids.add(template.id)
            templates.append(template)
        return templates

    def set_templates(self, templates: Iterable[FocusTemplate]) -> None:
        self._save_json("templates/items", [asdict(t) for t in templates])
        if self.active_template_id() and self.template_by_id(self.active_template_id()) is None:
            self.set_active_template_id("")

    def add_template(self, template: FocusTemplate) -> bool:
        if not template.id or not template.name.strip():
            return False
        templates = self.templates()
        if any(item.id == template.id for item in templates):
            return False
        templates.append(template)
        self.set_templates(templates)
        return True

    def delete_template(self, template_id: str) -> bool:
        if self.is_builtin_template(template_id):
            return False
        items = self.templates()
        cleaned = [item for item in items if item.id != str(template_id).strip()]
        if len(cleaned) == len(items):
            return False
        self.set_templates(cleaned)
        return True

    def update_template(self, template: FocusTemplate) -> bool:
        template_id = str(template.id).strip()
        if not template_id or not template.name.strip():
            return False
        items = self.templates()
        updated = False
        result: list[FocusTemplate] = []
        for current in items:
            if current.id == template_id:
                result.append(template)
                updated = True
            else:
                result.append(current)
        if not updated:
            return False
        self.set_templates(result)
        return True

    def is_builtin_template(self, template_id: str) -> bool:
        return str(template_id).strip() in builtin_template_ids()

    def template_by_id(self, template_id: str) -> FocusTemplate | None:
        for template in self.templates():
            if template.id == str(template_id).strip():
                return template
        return None

    def active_template_id(self) -> str:
        value = self._settings.value("templates/active_id", "")
        return str(value).strip() if value is not None else ""

    def set_active_template_id(self, template_id: str) -> None:
        self._settings.setValue("templates/active_id", str(template_id).strip())

    def _save_json(self, key: str, payload: object) -> None:
        self._settings.setValue(key, json.dumps(payload, ensure_ascii=False))

    def _load_json_value(self, raw: object) -> object:
        if not isinstance(raw, str) or not raw.strip():
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None
