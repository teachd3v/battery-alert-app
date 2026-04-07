# Battery Alert — Windows

Popup notifikasi baterai bergaya **glassmorphism** untuk Windows. Muncul otomatis saat baterai lemah atau sudah penuh, hilang sendiri saat kondisi berubah.

![Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4)
![Python](https://img.shields.io/badge/Python-3.8+-green)

---

## Cara Install

> Tidak perlu install Python atau software apapun. Cukup download dan double-click.

### 1. Download

**[⬇ Download BatteryAlert.exe](https://github.com/teachd3v/battery-alert-app/releases/latest/download/BatteryAlert.exe)**

### 2. Jalankan

Double-click `BatteryAlert.exe` → klik **Yes** saat muncul dialog → selesai.

App otomatis:
- Menyalin dirinya ke `%LocalAppData%\BatteryAlert\`
- Mendaftarkan ke startup Windows (registry)
- Langsung mulai memantau baterai di background

Tidak ada icon di taskbar atau tray — app berjalan diam-diam di background.

---

## Fitur

- Popup fullscreen saat baterai **≤ 20%** (tidak sedang dicas)
- Popup fullscreen saat baterai **≥ 90%** (sedang dicas — ingatkan cabut charger)
- Hilang otomatis saat kondisi berubah
- Auto-start setiap Windows login via registry

---

## Persyaratan

- Windows 10 / Windows 11
- Laptop dengan baterai

---

## Uninstall

Jalankan dari Command Prompt:

```cmd
"%LocalAppData%\BatteryAlert\BatteryAlert.exe" --uninstall
```

Lalu hapus folder secara manual:

```cmd
rmdir /s /q "%LocalAppData%\BatteryAlert"
```

Atau lewat **Task Manager** → tab **Startup** → klik kanan `BatteryAlert` → Disable.

---

## Test Popup

Cek tampilan sebelum kondisi baterai tercapai:

```cmd
"%LocalAppData%\BatteryAlert\BatteryAlert.exe" --test-low
"%LocalAppData%\BatteryAlert\BatteryAlert.exe" --test-full
```

---

## Konfigurasi

Edit nilai di bagian atas `battery_alert.py` lalu build ulang:

```python
THRESHOLD_LOW  = 20   # alert saat daya ≤ 20% (tidak dicas)
THRESHOLD_FULL = 90   # alert saat daya ≥ 90% (sedang dicas)
CHECK_SEC      = 30   # interval cek normal (detik)
DISMISS_SEC    = 5    # interval cek saat alert aktif (detik)
```

---

## Build dari Source (untuk developer)

Jika ingin build `.exe` sendiri:

```cmd
git clone https://github.com/teachd3v/battery-alert-app.git
cd battery-alert-app\windows
build.bat
```

> `build.bat` otomatis install PyInstaller dan menghasilkan `dist\BatteryAlert.exe`.
> File `.exe` di Releases dibangun otomatis via GitHub Actions setiap ada perubahan di `main`.

---

## Troubleshooting

**Popup tidak muncul**
- Pastikan laptop menggunakan baterai (tidak berlaku untuk PC desktop)
- Cek di Task Manager → Details → cari `BatteryAlert.exe`

**App tidak muncul saat startup**
- Buka `regedit` → `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
- Pastikan ada entry `BatteryAlert`

**Efek blur tidak muncul**
- Normal di Windows 10 versi lama — app tetap berfungsi dengan background solid
