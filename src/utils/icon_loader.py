import sys
from pathlib import Path

from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt


def resolve_asset_path(icon_name: str) -> str | None:
    module_asset_path = Path(__file__).resolve().parents[1] / "assets" / icon_name
    if module_asset_path.exists():
        return str(module_asset_path)

    meipass = getattr(sys, "_MEIPASS", None)
    if isinstance(meipass, str) and meipass:
        candidates = [
            Path(meipass) / "assets" / icon_name,
            Path(meipass) / "src" / "assets" / icon_name,
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
    return None


def load_app_icon(icon_name: str) -> QIcon:
    resource_path = f":/src/assets/{icon_name}"
    icon = QIcon(resource_path)
    if not icon.isNull():
        return icon

    asset_path = resolve_asset_path(icon_name)
    if asset_path is not None:
        icon = QIcon(asset_path)
        if not icon.isNull():
            return icon

    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    return QIcon(pixmap)
