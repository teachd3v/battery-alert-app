#!/usr/bin/env bash
# Install Battery Alert dengan systemd user service (persist reboot)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_SRC="$SCRIPT_DIR/battery_alert.py"
APP_DEST="$HOME/.local/bin/battery_alert.py"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/battery-alert.service"
UID_NUM=$(id -u)

echo "=== Battery Alert Installer ==="
echo ""

# ── 1. Salin script ──────────────────────────────────────────────────────────
mkdir -p "$HOME/.local/bin"
cp "$APP_SRC" "$APP_DEST"
chmod +x "$APP_DEST"
echo "[✓] Script disalin ke: $APP_DEST"

# ── 2. Buat systemd user service ─────────────────────────────────────────────
mkdir -p "$SERVICE_DIR"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Battery Alert — notifikasi baterai 20% dan 90%
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $APP_DEST
Restart=on-failure
RestartSec=10
Environment=DISPLAY=:0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/${UID_NUM}/bus
Environment=XDG_RUNTIME_DIR=/run/user/${UID_NUM}
Environment=XDG_SESSION_TYPE=x11
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal
SyslogIdentifier=battery-alert

[Install]
WantedBy=graphical-session.target
EOF
echo "[✓] Service file dibuat: $SERVICE_FILE"

# ── 3. Hapus autostart lama jika ada ─────────────────────────────────────────
DESKTOP_OLD="$HOME/.config/autostart/battery-alert.desktop"
[ -f "$DESKTOP_OLD" ] && rm -f "$DESKTOP_OLD" && echo "[✓] Autostart .desktop lama dihapus"

# ── 4. Enable & start service ────────────────────────────────────────────────
systemctl --user daemon-reload
systemctl --user enable battery-alert.service
pkill -f "battery_alert.py" 2>/dev/null || true
sleep 0.5
systemctl --user start battery-alert.service
echo "[✓] Service diaktifkan dan berjalan"

# ── 5. Status ─────────────────────────────────────────────────────────────────
echo ""
echo "=== Status ==="
systemctl --user status battery-alert.service --no-pager | head -8
echo ""
echo "Perintah berguna:"
echo "  systemctl --user status  battery-alert   # cek status"
echo "  systemctl --user stop    battery-alert   # stop sementara"
echo "  systemctl --user start   battery-alert   # start ulang"
echo "  systemctl --user disable battery-alert   # hapus dari autostart"
echo "  journalctl --user -u battery-alert -f    # lihat log live"
echo ""
echo "Test popup:"
echo "  python3 $APP_DEST --test-low"
echo "  python3 $APP_DEST --test-full"
