#!/usr/bin/env bash
# build.sh — Build BatteryAlert.app + BatteryAlert.dmg untuk macOS
# Jalankan di mesin macOS dengan Python 3.8+ terinstall
set -e

APP_NAME="BatteryAlert"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"
APP_PATH="$DIST_DIR/$APP_NAME.app"
DMG_PATH="$DIST_DIR/$APP_NAME.dmg"
DMG_STAGING="$SCRIPT_DIR/dmg_staging"

echo "========================================="
echo "  Battery Alert — macOS Build Script"
echo "========================================="
echo ""

# ── Cek Python ──
if ! command -v python3 &>/dev/null; then
    echo "[!] Python3 tidak ditemukan. Install dari https://python.org"
    exit 1
fi

# ── Cek / install PyInstaller ──
if ! python3 -c "import PyInstaller" &>/dev/null; then
    echo "[*] Menginstall PyInstaller..."
    pip3 install pyinstaller
fi

# ── Bersihkan build sebelumnya ──
echo "[*] Membersihkan build sebelumnya..."
rm -rf "$DIST_DIR" "$SCRIPT_DIR/build" "$SCRIPT_DIR/__pycache__" \
       "$DMG_STAGING" "$SCRIPT_DIR/$APP_NAME.spec"

# ── Build .app bundle ──
echo "[*] Membangun $APP_NAME.app ..."
pyinstaller \
    --windowed \
    --name "$APP_NAME" \
    --distpath "$DIST_DIR" \
    --workpath "$SCRIPT_DIR/build" \
    --specpath "$SCRIPT_DIR/build" \
    --clean \
    "$SCRIPT_DIR/battery_alert.py"

if [ ! -d "$APP_PATH" ]; then
    echo "[!] Build gagal — $APP_PATH tidak ditemukan."
    exit 1
fi

echo "[✓] $APP_NAME.app berhasil dibuat."

# ── Buat .dmg ──
echo "[*] Membuat $APP_NAME.dmg ..."

mkdir -p "$DMG_STAGING"
cp -r "$APP_PATH" "$DMG_STAGING/"

# Symlink ke /Applications untuk drag-and-drop install
ln -s /Applications "$DMG_STAGING/Applications"

hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$DMG_STAGING" \
    -ov \
    -format UDZO \
    "$DMG_PATH"

# Bersihkan staging
rm -rf "$DMG_STAGING" "$SCRIPT_DIR/build"

echo ""
echo "========================================="
echo "  Build selesai!"
echo "  Output: $DMG_PATH"
echo "========================================="
echo ""
echo "Distribusi ke teman-teman:"
echo "  1. Bagikan file: dist/BatteryAlert.dmg"
echo "  2. Buka DMG → drag BatteryAlert ke Applications"
echo "  3. Buka BatteryAlert dari Applications → klik Ya"
echo "  4. App otomatis running saat login macOS"
echo ""
echo "Test popup:"
echo "  open '$APP_PATH' --args --test-low"
echo "  open '$APP_PATH' --args --test-full"
echo ""
echo "Uninstall:"
echo "  open '$APP_PATH' --args --uninstall"
echo ""
