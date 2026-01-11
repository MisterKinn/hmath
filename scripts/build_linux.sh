#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[build] Installing python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt pyinstaller Pillow || true

# Ensure icon.png exists (generate from .icns if possible)
python3 - <<'PY'
from pathlib import Path
try:
    from PIL import Image
except Exception:
    print('Pillow not available; skipping icon conversion')
    Image = None
icns = Path('gui/icon.icns')
png = Path('gui/icon.png')
if icns.exists():
    if not png.exists() and Image is not None:
        try:
            im = Image.open(icns)
            # Choose a size that keeps detail
            im.save(png, 'PNG')
            print('Generated gui/icon.png from gui/icon.icns')
        except Exception as e:
            print('Failed to convert icon.icns to icon.png: ', e)
    elif not png.exists():
        print('Pillow not available; cannot generate gui/icon.png')
    else:
        print('gui/icon.png already exists')
else:
    print('gui/icon.icns not found; ensure gui/icon.png exists')
PY

# Build with PyInstaller using Linux spec
echo "[build] Running PyInstaller..."
set -x
python3 -m PyInstaller --noconfirm --log-level=DEBUG packaging/Formulite-linux.spec || { echo "[build] PyInstaller failed; aborting"; set +x; exit 1; }
set +x

# Validate build output
if [ -d "dist/Formulite" ]; then
  echo "[build] PyInstaller created dist/Formulite"
elif [ -d "dist" ]; then
  echo "[build] dist exists, contents:"
  ls -la dist || true
else
  echo "[build] No dist directory found after PyInstaller; aborting"
  exit 1
fi

# Prepare AppDir
APPDIR="$ROOT/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/512x512/apps"

# Copy PyInstaller output
echo "[build] Copying built files to AppDir/usr/bin..."
# dist/Formulite may be a directory or files; copy entire directory contents
if [ -d "dist/Formulite" ]; then
  cp -r dist/Formulite/* "$APPDIR/usr/bin/"
else
  cp -r dist/* "$APPDIR/usr/bin/"
fi

# Ensure executable name is Formulite
if [ -f "$APPDIR/usr/bin/Formulite" ]; then
  chmod +x "$APPDIR/usr/bin/Formulite"
fi

# Create desktop file from template
sed "s|%ROOT%|$ROOT|g" packaging/formulite.desktop.in > "$APPDIR/usr/share/applications/formulite.desktop"

# Install icon
if [ -f "gui/icon.png" ]; then
  cp gui/icon.png "$APPDIR/usr/share/icons/hicolor/512x512/apps/formulite.png"
else
  echo "Warning: gui/icon.png not found; AppImage icon may be missing"
fi

# Download linuxdeployqt if necessary
LDQ="linuxdeployqt-7-x86_64.AppImage"
if [ ! -f "$LDQ" ]; then
  echo "[build] Checking linuxdeployqt release URL..."
  http_status=$(curl -s -o /dev/null -w "%{http_code}" "https://github.com/linuxdeploy/linuxdeployqt/releases/download/7/linuxdeployqt-7-x86_64.AppImage")
  echo "[build] linuxdeployqt HTTP status: $http_status"
  if [ "$http_status" -ne 200 ]; then
    echo "[build] linuxdeployqt release not found (HTTP $http_status); aborting. Please verify the download URL in the script."
    exit 1
  fi
  echo "[build] Downloading linuxdeployqt..."
  wget --tries=3 -O "$LDQ" "https://github.com/linuxdeploy/linuxdeployqt/releases/download/7/linuxdeployqt-7-x86_64.AppImage"
  chmod +x "$LDQ"
  echo "[build] Downloaded $LDQ (size: $(stat -c%s "$LDQ" 2>/dev/null || stat -f%z "$LDQ"))"
  file "$LDQ" || true
fi

# Run linuxdeployqt to bundle Qt libs and create AppImage
echo "[build] Running linuxdeployqt to produce AppImage (this may take a while)..."
# Use the desktop file as the entrypoint
set +e
./$LDQ "$APPDIR/usr/share/applications/formulite.desktop" -appimage
if [ $? -ne 0 ]; then
  echo "[build] linuxdeployqt failed, retrying with --appimage-extract-and-run..."
  ./$LDQ --appimage-extract-and-run "$APPDIR/usr/share/applications/formulite.desktop" -appimage
fi
set -e

echo "[build] Done. Generated AppImage(s) should be in the current directory."
