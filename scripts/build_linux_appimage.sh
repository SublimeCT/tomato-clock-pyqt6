#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERSION="$(uv run python -c "import tomllib; print(tomllib.loads(open('pyproject.toml','rb').read().decode('utf-8'))['project']['version'])")"
ARCH="$(uname -m)"
APPDIR="dist/AppDir"
APPIMAGE_TOOL="build/appimagetool-${ARCH}.AppImage"
APPIMAGE_NAME="TomatoClock-${VERSION}-Linux-${ARCH}.AppImage"
APPIMAGE_PATH="dist/${APPIMAGE_NAME}"

rm -rf build dist
uv run pyinstaller \
  --name TomatoClock \
  --windowed \
  --clean \
  --noconfirm \
  --add-data "pyproject.toml:." \
  src/main.py

mkdir -p "${APPDIR}/usr/bin" "${APPDIR}/usr/share/applications" "${APPDIR}/usr/share/icons/hicolor/256x256/apps" "${APPDIR}/usr/share/metainfo"
cp -R dist/TomatoClock/. "${APPDIR}/usr/bin/"
install -m 755 packaging/linux/AppRun "${APPDIR}/AppRun"
install -m 644 packaging/linux/TomatoClock.desktop "${APPDIR}/TomatoClock.desktop"
install -m 644 packaging/linux/TomatoClock.desktop "${APPDIR}/usr/share/applications/TomatoClock.desktop"
install -m 644 packaging/linux/tomatoclock.appdata.xml "${APPDIR}/usr/share/metainfo/tomatoclock.appdata.xml"
install -m 644 src/assets/app-icon-256.png "${APPDIR}/TomatoClock.png"
install -m 644 src/assets/app-icon-256.png "${APPDIR}/usr/share/icons/hicolor/256x256/apps/TomatoClock.png"
chmod +x "${APPDIR}/usr/bin/TomatoClock"

if [[ ! -f "${APPIMAGE_TOOL}" ]]; then
  mkdir -p build
  curl -L "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage" -o "${APPIMAGE_TOOL}"
  chmod +x "${APPIMAGE_TOOL}"
fi

rm -f "${APPIMAGE_PATH}" "${APPIMAGE_PATH}.sha256"
ARCH="${ARCH}" APPIMAGETOOL_EXTRACT_AND_RUN=1 "${APPIMAGE_TOOL}" "${APPDIR}" "${APPIMAGE_PATH}"
chmod +x "${APPIMAGE_PATH}"
shasum -a 256 "${APPIMAGE_PATH}" > "${APPIMAGE_PATH}.sha256"
echo "Created ${APPIMAGE_PATH}"
