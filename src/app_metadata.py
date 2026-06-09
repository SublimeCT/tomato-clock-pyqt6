from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppMetadata:
    app_name: str
    display_name: str
    version: str
    organization_name: str
    organization_domain: str
    desktop_file_name: str
    repository_url: str


def _project_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[1]


def read_project_version() -> str:
    try:
        import tomllib
    except Exception:
        return "0.0.0"

    try:
        pyproject_path = _project_root() / "pyproject.toml"
        if pyproject_path.exists():
            raw = pyproject_path.read_bytes()
            data = tomllib.loads(raw.decode("utf-8"))
            version = data.get("project", {}).get("version", None)
            if isinstance(version, str) and version.strip():
                return version.strip()
    except Exception:
        pass

    try:
        from importlib.metadata import PackageNotFoundError, version

        for dist_name in ("tomato-clock-pyqt6", "tomato_clock_pyqt6"):
            try:
                current_version = version(dist_name)
                if isinstance(current_version, str) and current_version.strip():
                    return current_version.strip()
            except PackageNotFoundError:
                continue
    except Exception:
        pass

    return "0.0.0"


def get_app_metadata() -> AppMetadata:
    return AppMetadata(
        app_name="TomatoClock",
        display_name="番茄专注",
        version=read_project_version(),
        organization_name="SublimeCT",
        organization_domain="xiaban.run",
        desktop_file_name="TomatoClock",
        repository_url="https://github.com/SublimeCT/tomato-clock-pyqt6",
    )
