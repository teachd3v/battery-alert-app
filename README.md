# Battery Alert

Popup notifikasi baterai bergaya **glassmorphism**. Muncul otomatis saat baterai lemah atau sudah penuh, dan hilang sendiri saat kondisi berubah.

![Linux](https://img.shields.io/badge/Linux-GTK4-blue)
![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D4)
![macOS](https://img.shields.io/badge/macOS-10.13+-lightgrey)
![Python](https://img.shields.io/badge/Python-3.8+-green)

---

## Download

| OS | File | Cara Install |
|---|---|---|
| Windows 10/11 | [BatteryAlert.exe](https://github.com/teachd3v/battery-alert-app/releases/latest/download/BatteryAlert.exe) | Double-click → klik **Yes** → selesai |
| macOS 10.13+ | [BatteryAlert.dmg](https://github.com/teachd3v/battery-alert-app/releases/latest/download/BatteryAlert.dmg) | Buka DMG → drag ke Applications → buka → klik **Ya** |
| Linux | — | Lihat [linux/README.md](linux/README.md) |

> File `.exe` dan `.dmg` dibangun otomatis via GitHub Actions setiap ada update.

---

## Panduan per Platform

| OS | Folder | README |
|---|---|---|
| Linux | [`linux/`](linux/) | [linux/README.md](linux/README.md) |
| Windows | [`windows/`](windows/) | [windows/README.md](windows/README.md) |
| macOS | [`macos/`](macos/) | [macos/README.md](macos/README.md) |

---

## Fitur

- Popup fullscreen saat baterai **≤ 20%** (tidak sedang dicas)
- Popup fullscreen saat baterai **≥ 90%** (sedang dicas — ingatkan cabut charger)
- Hilang otomatis saat kondisi berubah
- UI glassmorphism dengan animasi pulse
- Auto-start setiap login/startup

---

## Lisensi

Didistribusikan tanpa garansi. Bebas digunakan dan dimodifikasi.
