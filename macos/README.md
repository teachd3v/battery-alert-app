# Battery Alert — macOS

Popup notifikasi baterai bergaya **glassmorphism** untuk macOS. Muncul otomatis saat baterai lemah atau sudah penuh, hilang sendiri saat kondisi berubah.

![macOS](https://img.shields.io/badge/Platform-macOS-lightgrey)
![Python](https://img.shields.io/badge/Python-3.8+-green)

---

## Cara Install (untuk pengguna)

> Tidak perlu install Python. Cukup download file `.dmg`.

1. Download **[BatteryAlert.dmg](https://github.com/teachd3v/battery-alert-app/releases/latest/download/BatteryAlert.dmg)**
2. Buka file `.dmg`
3. Drag **BatteryAlert** ke folder **Applications**
4. Buka **BatteryAlert** dari Applications
5. Klik **Ya** saat muncul dialog konfirmasi
6. App otomatis berjalan di background dan aktif setiap login

> **Catatan Gatekeeper:** Jika muncul peringatan "tidak dapat dibuka karena berasal dari developer yang tidak dikenal", klik kanan `BatteryAlert.app` → pilih **Open** → klik **Open** lagi.

---

## Fitur

- Popup fullscreen saat baterai **≤ 20%** (tidak sedang dicas)
- Popup fullscreen saat baterai **≥ 90%** (sedang dicas — ingatkan cabut charger)
- Hilang otomatis saat kondisi berubah
- Berjalan diam-diam di background (tidak ada icon di menu bar)
- Auto-start setiap login via **LaunchAgent**

---

## Persyaratan

- macOS 10.13 High Sierra atau lebih baru
- MacBook / Mac dengan baterai
- Python 3.8+ (hanya untuk build dari source)

---

## Build dari Source (untuk developer)

Jika ingin build `.dmg` sendiri:

### 1. Pastikan Python 3 terinstall

```bash
python3 --version
```

Jika belum ada, download dari [python.org](https://www.python.org/downloads/macos/).

### 2. Clone repo

```bash
git clone https://github.com/teachd3v/battery-alert-app.git
cd battery-alert-app/macos
```

### 3. Jalankan build script

```bash
chmod +x build.sh
./build.sh
```

Script akan otomatis:
- Install PyInstaller jika belum ada
- Build `dist/BatteryAlert.app`
- Buat `dist/BatteryAlert.dmg` (siap distribusi)

### 4. Distribusikan

Bagikan file `dist/BatteryAlert.dmg` — penerima tinggal ikuti langkah install di atas.

---

## Test Popup

Cek tampilan tanpa menunggu kondisi baterai:

```bash
open /Applications/BatteryAlert.app --args --test-low
open /Applications/BatteryAlert.app --args --test-full
```

---

## Uninstall

```bash
open /Applications/BatteryAlert.app --args --uninstall
```

Lalu hapus app:

```bash
rm -rf /Applications/BatteryAlert.app
```

Atau manual:
1. Buka **System Settings** → **General** → **Login Items**
2. Hapus `Battery Alert` dari daftar *(jika muncul di sana)*
3. Hapus file plist: `~/Library/LaunchAgents/com.batteryalert.plist`
4. Hapus `BatteryAlert.app` dari Applications

---

## Konfigurasi

Edit nilai di bagian atas `battery_alert.py` sebelum build:

```python
THRESHOLD_LOW  = 20   # alert saat daya ≤ 20% (tidak dicas)
THRESHOLD_FULL = 90   # alert saat daya ≥ 90% (sedang dicas)
CHECK_SEC      = 30   # interval cek normal (detik)
DISMISS_SEC    = 5    # interval cek saat alert aktif (detik)
```

Setelah edit, jalankan `build.sh` ulang untuk generate dmg baru.

---

## Cara Kerja

| Kondisi | Aksi |
|---|---|
| Baterai ≤ 20% + tidak dicas | Popup merah muncul |
| Charger dipasang | Popup merah hilang |
| Baterai ≥ 90% + sedang dicas | Popup hijau muncul |
| Charger dicabut | Popup hijau hilang |

App berjalan via **LaunchAgent** (`~/Library/LaunchAgents/com.batteryalert.plist`) yang di-load otomatis saat login.

---

## Troubleshooting

**Popup tidak muncul**
- Pastikan kamu menggunakan MacBook (bukan Mac desktop tanpa baterai)
- Cek apakah app berjalan: `pgrep -a BatteryAlert`
- Lihat log: `cat /tmp/battery-alert.log`

**App tidak muncul saat startup**
- Cek plist: `cat ~/Library/LaunchAgents/com.batteryalert.plist`
- Load ulang: `launchctl load -w ~/Library/LaunchAgents/com.batteryalert.plist`

**Gatekeeper memblokir app**
- Klik kanan `BatteryAlert.app` → **Open** → **Open**
- Atau jalankan: `xattr -d com.apple.quarantine /Applications/BatteryAlert.app`
