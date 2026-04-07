@echo off
:: build.bat — Build BatteryAlert.exe menggunakan PyInstaller
:: Jalankan file ini di Windows untuk menghasilkan installer .exe
setlocal
set "SCRIPT_DIR=%~dp0"
set "APP_NAME=BatteryAlert"
set "OUTPUT_DIR=%SCRIPT_DIR%dist"

echo =========================================
echo   Battery Alert — Windows Build Script
echo =========================================
echo.

:: ── Cek Python ──
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python tidak ditemukan. Install dari https://python.org
    pause
    exit /b 1
)

:: ── Cek / install PyInstaller ──
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [*] Menginstall PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [!] Gagal install PyInstaller.
        pause
        exit /b 1
    )
)

:: ── Build .exe ──
echo [*] Membangun %APP_NAME%.exe ...
echo.
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "%APP_NAME%" ^
    --distpath "%OUTPUT_DIR%" ^
    --workpath "%SCRIPT_DIR%build_temp" ^
    --specpath "%SCRIPT_DIR%build_temp" ^
    --clean ^
    "%SCRIPT_DIR%battery_alert.py"

if errorlevel 1 (
    echo.
    echo [!] Build GAGAL. Periksa error di atas.
    pause
    exit /b 1
)

:: ── Hapus file temp ──
rmdir /s /q "%SCRIPT_DIR%build_temp" 2>nul

echo.
echo =========================================
echo   Build selesai!
echo   Output: %OUTPUT_DIR%\%APP_NAME%.exe
echo =========================================
echo.
echo Cara distribusi ke teman-teman:
echo   1. Bagikan file: dist\BatteryAlert.exe
echo   2. Mereka cukup double-click untuk install
echo   3. App otomatis masuk startup Windows
echo.
echo Test popup sebelum distribusi:
echo   dist\BatteryAlert.exe --test-low
echo   dist\BatteryAlert.exe --test-full
echo.
echo Uninstall (hapus dari startup):
echo   dist\BatteryAlert.exe --uninstall
echo.
pause
