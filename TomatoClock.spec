# -*- mode: python ; coding: utf-8 -*-

import tomllib
from pathlib import Path


project_root = Path(SPECPATH)


def read_version() -> str:
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return "0.0.0"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version", "0.0.0")
    return str(version)


app_version = read_version()


a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('pyproject.toml', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TomatoClock',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='TomatoClock',
)
app = BUNDLE(
    coll,
    name='TomatoClock.app',
    icon='icon.icns',
    bundle_identifier='com.sublimect.tomatoclock',
    info_plist={
        'CFBundleName': 'TomatoClock',
        'CFBundleDisplayName': '番茄专注',
        'CFBundleShortVersionString': app_version,
        'CFBundleVersion': app_version,
        'NSHighResolutionCapable': True,
    },
)
