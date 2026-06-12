from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

DEFAULT_FOCUS_END_PROMPT = "本轮专注完成，短暂休息片刻"
DEFAULT_BREAK_END_PROMPT = "电量满格，重新出发啦！"
BUILTIN_FOCUS_PROMPT_ID = "builtin-focus-end"
BUILTIN_BREAK_PROMPT_ID = "builtin-break-end"


@dataclass(frozen=True)
class FocusTemplate:
    id: str
    name: str
    emoji: str
    focus_minutes: int
    short_break_minutes: int
    long_break_minutes: int
    rounds: int


def default_templates() -> list[FocusTemplate]:
    return [
        FocusTemplate("classic", "经典番茄钟", "🍅", 25, 5, 15, 4),
        FocusTemplate("deep-work", "深度工作", "🔥", 50, 10, 30, 3),
        FocusTemplate("sprint", "极速冲刺", "⚡", 15, 3, 10, 6),
    ]


def builtin_template_ids() -> set[str]:
    return {template.id for template in default_templates()}


def sanitize_prompts(prompts: Iterable[str], fallback: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in prompts:
        text = str(item).strip()
        if not text or text in seen:
            continue
        result.append(text[:50])
        seen.add(text)
        if len(result) >= 10:
            break
    return result or [fallback]


def template_from_dict(item: object) -> FocusTemplate | None:
    if not isinstance(item, dict):
        return None
    try:
        name = str(item.get("name", "")).strip()
        template = FocusTemplate(
            id=str(item.get("id", "")).strip(),
            name=name,
            emoji=str(item.get("emoji", "")).strip() or "🍅",
            focus_minutes=max(1, min(180, int(item.get("focus_minutes", 25)))),
            short_break_minutes=max(1, min(60, int(item.get("short_break_minutes", 5)))),
            long_break_minutes=max(1, min(90, int(item.get("long_break_minutes", 15)))),
            rounds=max(1, min(12, int(item.get("rounds", 4)))),
        )
    except Exception:
        return None
    return template if template.id and template.name else None
