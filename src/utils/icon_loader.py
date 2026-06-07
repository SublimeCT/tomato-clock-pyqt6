import sys
from pathlib import Path

from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt


def load_app_icon(icon_name: str) -> QIcon:
    resource_path = f":/src/assets/{icon_name}"
    icon = QIcon(resource_path)
    if not icon.isNull():
        return icon

    module_asset_path = Path(__file__).resolve().parents[1] / "assets" / icon_name
    icon = QIcon(str(module_asset_path))
    if not icon.isNull():
        return icon

    meipass = getattr(sys, "_MEIPASS", None)
    if isinstance(meipass, str) and meipass:
        candidates = [
            Path(meipass) / "assets" / icon_name,
            Path(meipass) / "src" / "assets" / icon_name,
        ]
        for candidate in candidates:
            icon = QIcon(str(candidate))
            if not icon.isNull():
                return icon

    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    return QIcon(pixmap)
