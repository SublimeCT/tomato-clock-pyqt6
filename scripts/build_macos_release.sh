#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERSION="$(uv run python -c "import tomllib; print(tomllib.loads(open('pyproject.toml','rb').read().decode('utf-8'))['project']['version'])")"
APP_NAME="TomatoClock"
APP_PATH="dist/${APP_NAME}.app"
STAGING_DIR="dist/dmg-root"
DMG_NAME="${APP_NAME}-${VERSION}-macOS.dmg"
DMG_PATH="dist/${DMG_NAME}"

rm -rf build dist
uv run pyinstaller TomatoClock.spec --clean --noconfirm

if [[ -n "${APPLE_CODESIGN_IDENTITY:-}" ]]; then
  codesign --force --deep --options runtime --sign "${APPLE_CODESIGN_IDENTITY}" "${APP_PATH}"
fi

rm -rf "${STAGING_DIR}" "${DMG_PATH}" "${DMG_PATH}.sha256"
mkdir -p "${STAGING_DIR}"
ditto "${APP_PATH}" "${STAGING_DIR}/${APP_NAME}.app"
ln -s /Applications "${STAGING_DIR}/Applications"

hdiutil create \
  -volname "TomatoClock" \
  -srcfolder "${STAGING_DIR}" \
  -ov \
  -format UDZO \
  "${DMG_PATH}"

shasum -a 256 "${DMG_PATH}" > "${DMG_PATH}.sha256"
echo "Created ${DMG_PATH}"
