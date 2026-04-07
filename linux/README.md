# Battery Alert — Linux GTK4

Popup notifikasi baterai bergaya **glassmorphism** untuk Linux. Muncul otomatis saat baterai lemah atau sudah penuh, dan hilang sendiri saat kondisi berubah.

![Linux](https://img.shields.io/badge/Platform-Linux-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![GTK](https://img.shields.io/badge/GTK-4.0-orange)

---

## Fitur

- Popup fullscreen saat baterai **≤ 20%** (tidak sedang dicas)
- Popup fullscreen saat baterai **≥ 90%** (sedang dicas — ingatkan cabut charger)
- Hilang otomatis saat kondisi berubah (tidak perlu ditutup manual)
- UI glassmorphism dengan animasi pulse
- Berjalan sebagai **systemd user service** (aktif otomatis setiap login)

---

## Persyaratan

- Linux dengan **systemd** (Ubuntu, Debian, Fedora, Arch, dll.)
- Python 3.8+
- GTK 4.0
- Baterai terdeteksi di `/sys/class/power_supply/`

---

## Dependensi

Install dependensi jika belum ada:

```bash
# Ubuntu / Debian
sudo apt install python3 python3-gi gir1.2-gtk-4.0

# Fedora
sudo dnf install python3 python3-gobject gtk4

# Arch
sudo pacman -S python python-gobject gtk4
```

---

## Instalasi

### Cara 1 — Script install (direkomendasikan)

```bash
git clone https://github.com/teachd3v/battery-alert-app.git
cd battery-alert-app/linux
chmod +x install.sh
./install.sh
```

Script akan:
- Menyalin script ke `~/.local/bin/`
- Membuat systemd user service
- Mengaktifkan dan menjalankan service secara otomatis

---

### Cara 2 — Paket `.deb` (Ubuntu/Debian)

Build paket terlebih dahulu:

```bash
chmod +x build-deb.sh
./build-deb.sh
```

Lalu install:

```bash
sudo dpkg -i battery-alert_1.0.0_all.deb
```

Uninstall:

```bash
sudo apt remove battery-alert
```

---

## Perintah Berguna

```bash
# Cek status service
systemctl --user status battery-alert

# Stop sementara
systemctl --user stop battery-alert

# Start ulang
systemctl --user start battery-alert

# Hapus dari autostart
systemctl --user disable battery-alert

# Lihat log live
journalctl --user -u battery-alert -f
```

---

## Test Popup

Cek tampilan popup tanpa menunggu kondisi baterai:

```bash
# Test popup baterai lemah
python3 ~/.local/bin/battery_alert.py --test-low

# Test popup baterai penuh
python3 ~/.local/bin/battery_alert.py --test-full
```

Jika install via `.deb`:

```bash
battery-alert --test-low
battery-alert --test-full
```

---

## Konfigurasi

Edit nilai threshold di bagian atas `battery_alert.py`:

```python
THRESHOLD_LOW  = 20      # alert saat daya ≤ 20% (tidak dicas)
THRESHOLD_FULL = 90      # alert saat daya ≥ 90% (sedang dicas)
CHECK_MS       = 30_000  # interval cek normal (30 detik)
DISMISS_MS     = 5_000   # interval cek saat alert aktif (5 detik)
```

Setelah mengubah, restart service:

```bash
systemctl --user restart battery-alert
```
