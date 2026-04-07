# Activity Log — Battery Alert App

Log aktivitas pengembangan project via Claude Code CLI.

---

## 2026-04-08

### Sesi: Setup awal & multi-platform development

**[1] Inisialisasi repo GitHub**
- Init git repo baru di `battery-alert-app/`
- Buat `.gitignore` (abaikan `__pycache__`, `.deb`, folder build)
- Buat `README.md` panduan Linux (install, dependensi, perintah, konfigurasi)
- Push ke GitHub: `https://github.com/teachd3v/battery-alert-app`

**[2] Tambah versi Windows**
- Buat `windows/battery_alert.py` — tkinter + Windows API (`GetSystemPowerStatus`)
- Buat `windows/build.bat` — build script PyInstaller untuk developer
- Buat `windows/README.md` — panduan Windows
- Fitur: auto-install ke `%LocalAppData%\BatteryAlert\`, startup via registry

**[3] Reorganisasi folder**
- Pindahkan semua file Linux ke folder `linux/`
- Buat `linux/README.md` — panduan khusus Linux
- Update README utama jadi tabel navigasi per OS

**[4] Tambah versi macOS**
- Buat `macos/battery_alert.py` — tkinter + `pmset` untuk baca baterai
- Buat `macos/build.sh` — build script PyInstaller → `.app` → `.dmg`
- Buat `macos/README.md` — panduan macOS
- Fitur: dialog native via `osascript`, startup via LaunchAgent plist

**[5] GitHub Actions CI/CD**
- Buat `.github/workflows/build-release.yml`
- Build otomatis `BatteryAlert.exe` (Windows runner) dan `BatteryAlert.dmg` (macOS runner)
- Publish ke GitHub Releases tag `latest` setiap push ke `main`
- Update README dengan tabel download langsung per platform

---

## Struktur Akhir

```
battery-alert-app/
├── .github/
│   └── workflows/
│       └── build-release.yml   ← CI/CD auto-build & release
├── linux/
│   ├── battery_alert.py        ← GTK4 + systemd
│   ├── install.sh              ← installer via systemd user service
│   ├── build-deb.sh            ← builder paket .deb
│   └── README.md
├── windows/
│   ├── battery_alert.py        ← tkinter + Windows API
│   ├── build.bat               ← build script PyInstaller (developer)
│   └── README.md
├── macos/
│   ├── battery_alert.py        ← tkinter + pmset
│   ├── build.sh                ← build script → .app + .dmg
│   └── README.md
├── .gitignore
├── ACTIVITY_LOG.md             ← file ini
└── README.md                   ← tabel navigasi + link download
```

---

## Commit History

| Hash | Pesan |
|---|---|
| `253f9b2` | feat: battery alert app with glassmorphism GTK4 popup |
| `f604bac` | feat: add Windows version with auto-install and startup registry |
| `5f92ee6` | refactor: reorganize into linux/ and windows/ folders |
| `980f381` | feat: add macOS version with DMG installer and LaunchAgent startup |
| `c30719e` | feat: add GitHub Actions CI/CD for auto-build EXE and DMG on release |

---

## Teknologi per Platform

| Platform | UI | Baca Baterai | Startup |
|---|---|---|---|
| Linux | GTK4 (python-gi) | `/sys/class/power_supply/` | systemd user service |
| Windows | tkinter + ctypes | `GetSystemPowerStatus` WinAPI | Registry `HKCU\...\Run` |
| macOS | tkinter | `pmset -g batt` | LaunchAgent plist |
