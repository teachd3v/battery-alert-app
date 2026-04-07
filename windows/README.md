# Battery Alert — Windows

Popup notifikasi baterai untuk Windows. Muncul otomatis saat baterai lemah atau sudah penuh, hilang sendiri saat kondisi berubah.

![Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)

---

## Cara Install (untuk pengguna)

> Tidak perlu install Python. Cukup download file `.exe`.

1. Download **`BatteryAlert.exe`** dari [Releases](https://github.com/teachd3v/battery-alert-app/releases)
2. Double-click file tersebut
3. Klik **Yes** saat muncul dialog konfirmasi
4. App otomatis terinstall ke `%LocalAppData%\BatteryAlert\` dan berjalan setiap startup Windows

Selesai — tidak perlu konfigurasi apapun.

---

## Fitur

- Popup fullscreen saat baterai **≤ 20%** (tidak sedang dicas)
- Popup fullscreen saat baterai **≥ 90%** (sedang dicas — ingatkan cabut charger)
- Hilang otomatis saat kondisi berubah
- Berjalan diam-diam di background tanpa icon tray
- Auto-start setiap Windows login via registry

---

## Persyaratan

- Windows 10 / Windows 11
- Laptop dengan baterai (tidak berlaku untuk PC desktop)

---

## Build dari Source (untuk developer)

Jika ingin build `.exe` sendiri:

### 1. Install Python

Download dari [python.org](https://www.python.org/downloads/) — pastikan centang **"Add Python to PATH"** saat install.

### 2. Clone repo

```cmd
git clone https://github.com/teachd3v/battery-alert-app.git
cd battery-alert-app\windows
```

### 3. Jalankan build script

```cmd
build.bat
```

Script akan otomatis:
- Install PyInstaller jika belum ada
- Build `dist\BatteryAlert.exe`
- Hapus file build sementara

### 4. Distribusikan

Bagikan file `dist\BatteryAlert.exe` ke teman-teman — mereka tinggal double-click.

---

## Test Popup

Cek tampilan tanpa menunggu kondisi baterai:

```cmd
BatteryAlert.exe --test-low
BatteryAlert.exe --test-full
```

---

## Uninstall

```cmd
BatteryAlert.exe --uninstall
```

Atau manual:
1. Hapus folder `%LocalAppData%\BatteryAlert\`
2. Buka **Task Manager** → tab **Startup** → disable `BatteryAlert`

---

## Konfigurasi

Edit nilai di bagian atas `battery_alert.py` sebelum build:

```python
THRESHOLD_LOW  = 20   # alert saat daya ≤ 20% (tidak dicas)
THRESHOLD_FULL = 90   # alert saat daya ≥ 90% (sedang dicas)
CHECK_SEC      = 30   # interval cek normal (detik)
DISMISS_SEC    = 5    # interval cek saat alert aktif (detik)
```

Setelah edit, jalankan `build.bat` ulang untuk generate exe baru.

---

## Cara Kerja

| Kondisi | Aksi |
|---|---|
| Baterai ≤ 20% + tidak dicas | Popup merah muncul |
| Charger dipasang | Popup merah hilang |
| Baterai ≥ 90% + sedang dicas | Popup hijau muncul |
| Charger dicabut | Popup hijau hilang |

App berjalan di background (tidak ada icon di taskbar/tray). Cek via **Task Manager → Details → BatteryAlert.exe**.

---

## Troubleshooting

**Popup tidak muncul**
- Pastikan laptop menggunakan baterai (bukan desktop PC)
- Cek Task Manager apakah `BatteryAlert.exe` sudah running

**App tidak muncul saat startup**
- Buka `regedit` → `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
- Pastikan ada entry `BatteryAlert` yang menunjuk ke path yang benar

**Efek blur tidak muncul**
- Normal terjadi di Windows 10 versi lama — app tetap berfungsi dengan background solid
