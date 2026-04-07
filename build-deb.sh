#!/usr/bin/env bash
# build-deb.sh — Bangun paket .deb untuk Battery Alert
set -e

PKG_NAME="battery-alert"
PKG_VERSION="1.0.0"
PKG_ARCH="all"
PKG_DIR="${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}"

echo "=== Membangun paket .deb: ${PKG_NAME} v${PKG_VERSION} ==="
echo ""

# ── Bersihkan build sebelumnya ───────────────────────────────────────────────
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"

# ── Buat struktur direktori ──────────────────────────────────────────────────
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/lib/battery-alert"
mkdir -p "$PKG_DIR/usr/lib/systemd/user"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/doc/battery-alert"

# ── Salin script utama ───────────────────────────────────────────────────────
cp battery_alert.py "$PKG_DIR/usr/lib/battery-alert/battery_alert.py"
chmod 644 "$PKG_DIR/usr/lib/battery-alert/battery_alert.py"

# ── Buat launcher CLI ────────────────────────────────────────────────────────
cat > "$PKG_DIR/usr/bin/battery-alert" << 'LAUNCHER'
#!/usr/bin/env bash
exec /usr/bin/python3 /usr/lib/battery-alert/battery_alert.py "$@"
LAUNCHER
chmod 755 "$PKG_DIR/usr/bin/battery-alert"

# ── Buat systemd user service ────────────────────────────────────────────────
# %t = XDG_RUNTIME_DIR (/run/user/<uid>), otomatis di-resolve oleh systemd
cat > "$PKG_DIR/usr/lib/systemd/user/battery-alert.service" << 'SERVICE'
[Unit]
Description=Battery Alert — notifikasi baterai 20% dan 90%
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/lib/battery-alert/battery_alert.py
Restart=on-failure
RestartSec=10
Environment=DISPLAY=:0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=%t/bus
Environment=XDG_RUNTIME_DIR=%t
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal
SyslogIdentifier=battery-alert

[Install]
WantedBy=graphical-session.target
SERVICE

# ── File copyright ───────────────────────────────────────────────────────────
cat > "$PKG_DIR/usr/share/doc/battery-alert/copyright" << 'COPYRIGHT'
Battery Alert — Glassmorphism Battery Notification for Linux GTK4

Source code: https://github.com/huda-teach/battery-alert-app

This software is distributed as-is without warranty.
COPYRIGHT

# ── DEBIAN/control ───────────────────────────────────────────────────────────
cat > "$PKG_DIR/DEBIAN/control" << CONTROL
Package: ${PKG_NAME}
Version: ${PKG_VERSION}
Architecture: ${PKG_ARCH}
Maintainer: huda-teach <huda-teach@localhost>
Depends: python3 (>= 3.8), python3-gi, gir1.2-gtk-4.0
Description: Battery Alert — Glassmorphism popup notifikasi baterai
 Menampilkan popup fullscreen bergaya glassmorphism saat baterai:
 .
  * Lemah (≤ 20%) dan tidak sedang dicas
  * Penuh (≥ 90%) dan sedang dicas (ingatkan untuk cabut charger)
 .
 Berjalan sebagai systemd user service dan otomatis aktif saat login.
CONTROL

# ── DEBIAN/postinst — dijalankan setelah instalasi ──────────────────────────
cat > "$PKG_DIR/DEBIAN/postinst" << 'POSTINST'
#!/bin/bash
set -e

# Deteksi user nyata (bukan root) yang menjalankan sudo
REAL_USER="${SUDO_USER:-}"
if [ -z "$REAL_USER" ]; then
    # Coba deteksi dari sesi login aktif
    REAL_USER=$(logname 2>/dev/null || echo "")
fi

if [ -z "$REAL_USER" ] || [ "$REAL_USER" = "root" ]; then
    echo ""
    echo "┌─────────────────────────────────────────────────┐"
    echo "│  Battery Alert terinstal!                       │"
    echo "│                                                 │"
    echo "│  Aktifkan service sebagai user Anda:            │"
    echo "│    systemctl --user enable --now battery-alert  │"
    echo "└─────────────────────────────────────────────────┘"
    exit 0
fi

REAL_UID=$(id -u "$REAL_USER" 2>/dev/null || echo "")
if [ -z "$REAL_UID" ]; then
    echo "battery-alert: Tidak bisa mendapatkan UID untuk $REAL_USER"
    exit 0
fi

XDG_RT="/run/user/${REAL_UID}"
DBUS_ADDR="unix:path=${XDG_RT}/bus"

_run_user() {
    sudo -u "$REAL_USER" \
        XDG_RUNTIME_DIR="$XDG_RT" \
        DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
        systemctl --user "$@" 2>/dev/null || true
}

echo "battery-alert: Mengaktifkan service untuk user '$REAL_USER'..."

_run_user daemon-reload
_run_user enable battery-alert.service

if [ -d "$XDG_RT" ]; then
    _run_user start battery-alert.service
    echo ""
    echo "┌─────────────────────────────────────────────────────┐"
    echo "│  Battery Alert berhasil diinstal & berjalan!        │"
    echo "│                                                     │"
    echo "│  Perintah berguna:                                  │"
    echo "│    systemctl --user status battery-alert            │"
    echo "│    systemctl --user stop   battery-alert            │"
    echo "│    journalctl --user -u battery-alert -f            │"
    echo "│                                                     │"
    echo "│  Test popup:                                        │"
    echo "│    battery-alert --test-low                         │"
    echo "│    battery-alert --test-full                        │"
    echo "└─────────────────────────────────────────────────────┘"
else
    echo "battery-alert: Service akan aktif di login berikutnya."
fi
POSTINST
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# ── DEBIAN/prerm — dijalankan sebelum uninstall ──────────────────────────────
cat > "$PKG_DIR/DEBIAN/prerm" << 'PRERM'
#!/bin/bash
set -e

REAL_USER="${SUDO_USER:-}"
if [ -z "$REAL_USER" ]; then
    REAL_USER=$(logname 2>/dev/null || echo "")
fi
if [ -z "$REAL_USER" ] || [ "$REAL_USER" = "root" ]; then
    exit 0
fi

REAL_UID=$(id -u "$REAL_USER" 2>/dev/null || echo "")
if [ -z "$REAL_UID" ]; then exit 0; fi

XDG_RT="/run/user/${REAL_UID}"
DBUS_ADDR="unix:path=${XDG_RT}/bus"

_run_user() {
    sudo -u "$REAL_USER" \
        XDG_RUNTIME_DIR="$XDG_RT" \
        DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
        systemctl --user "$@" 2>/dev/null || true
}

echo "battery-alert: Menghentikan dan menonaktifkan service..."
_run_user stop battery-alert.service
_run_user disable battery-alert.service
_run_user daemon-reload

echo "battery-alert: Service dihentikan."
PRERM
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# ── Build .deb ───────────────────────────────────────────────────────────────
echo "Membangun paket..."
dpkg-deb --build --root-owner-group "$PKG_DIR"

echo ""
echo "======================================================"
echo "  Paket berhasil dibuat: ${PKG_DIR}.deb"
echo "======================================================"
echo ""
echo "Install:   sudo dpkg -i ${PKG_DIR}.deb"
echo "Uninstall: sudo apt remove battery-alert"
echo ""
