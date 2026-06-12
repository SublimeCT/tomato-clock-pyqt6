from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

from PyQt6.QtCore import QStandardPaths


@dataclass(frozen=True)
class FocusSession:
    started_at_iso: str
    completed_at_iso: str
    focus_type: str
    minutes: int
    template_name: str = ""


class SessionStore:
    def __init__(self):
        base_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
        base_dir.mkdir(parents=True, exist_ok=True)
        self._path = base_dir / "sessions.json"
        self._sessions = self._load()

    def _load(self) -> list[FocusSession]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return []
        sessions: list[FocusSession] = []
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict):
                    continue
                try:
                    sessions.append(
                        FocusSession(
                            started_at_iso=str(item.get("started_at_iso", "")),
                            completed_at_iso=str(item.get("completed_at_iso", "")),
                            focus_type=str(item.get("focus_type", "")),
                            minutes=int(item.get("minutes", 0)),
                            template_name=str(item.get("template_name", "")),
                        )
                    )
                except Exception:
                    continue
        return sessions

    def _save(self) -> None:
        payload = [asdict(s) for s in self._sessions]
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_session(
        self,
        focus_type: str,
        minutes: int,
        started_at: datetime,
        completed_at: datetime,
        template_name: str = "",
    ) -> None:
        self._sessions.append(
            FocusSession(
                started_at_iso=started_at.isoformat(timespec="seconds"),
                completed_at_iso=completed_at.isoformat(timespec="seconds"),
                focus_type=focus_type,
                minutes=int(minutes),
                template_name=str(template_name).strip(),
            )
        )
        self._save()

    def all_sessions(self) -> list[FocusSession]:
        return list(self._sessions)

    def years(self) -> list[int]:
        years: set[int] = set()
        for s in self._sessions:
            try:
                dt = datetime.fromisoformat(s.completed_at_iso)
            except Exception:
                continue
            years.add(dt.year)
        if not years:
            years.add(date.today().year)
        return sorted(years)

    def sessions_on(self, day: date) -> list[FocusSession]:
        prefix = day.isoformat()
        result: list[FocusSession] = []
        for s in self._sessions:
            if s.completed_at_iso.startswith(prefix):
                result.append(s)
        return result

    def sessions_between(self, start_day: date, end_day: date) -> list[FocusSession]:
        start = datetime.combine(start_day, datetime.min.time())
        end = datetime.combine(end_day, datetime.max.time())
        result: list[FocusSession] = []
        for s in self._sessions:
            try:
                dt = datetime.fromisoformat(s.completed_at_iso)
            except Exception:
                continue
            if start <= dt <= end:
                result.append(s)
        return result

    def counts_by_day(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for s in self._sessions:
            day = s.completed_at_iso[:10]
            if len(day) != 10:
                continue
            counts[day] = counts.get(day, 0) + 1
        return counts

    def minutes_by_day(self) -> dict[str, int]:
        minutes: dict[str, int] = {}
        for s in self._sessions:
            day = s.completed_at_iso[:10]
            if len(day) != 10:
                continue
            minutes[day] = minutes.get(day, 0) + int(s.minutes)
        return minutes
