#!/usr/bin/env python3
"""
Battery Alert — Windows
Glassmorphism-style popup saat baterai 20% (low) atau 90% saat dicas (full).
Popup hilang otomatis saat kondisi berubah.

Installer mode: jalankan exe sekali untuk auto-install ke AppData + startup registry.
"""

import sys
import os
import ctypes
import threading
import shutil
import subprocess
import time

try:
    import winreg
    import tkinter as tk
    from ctypes import Structure, c_byte, c_ulong, c_int, sizeof, pointer, POINTER, cast
except ImportError:
    sys.exit("ERROR: Script ini hanya untuk Windows.")

# ── Konstanta ──────────────────────────────────────────────────────────────
THRESHOLD_LOW  = 20       # alert saat daya ≤ 20% (tidak dicas)
THRESHOLD_FULL = 90       # alert saat daya ≥ 90% (sedang dicas)
CHECK_SEC      = 30       # interval cek normal (detik)
DISMISS_SEC    = 5        # interval cek saat alert aktif (detik)

INSTALL_DIR  = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'BatteryAlert')
INSTALL_PATH = os.path.join(INSTALL_DIR, 'BatteryAlert.exe')
REG_KEY      = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_VALUE    = "BatteryAlert"


# ── Baca baterai via Windows API ───────────────────────────────────────────
class SYSTEM_POWER_STATUS(Structure):
    _fields_ = [
        ('ACLineStatus',       c_byte),   # 0=offline, 1=online, 255=unknown
        ('BatteryFlag',        c_byte),   # bit flags
        ('BatteryLifePercent', c_byte),   # 0-100, 255=unknown
        ('SystemStatusFlag',   c_byte),
        ('BatteryLifeTime',    c_ulong),
        ('BatteryFullLifeTime',c_ulong),
    ]

def read_battery():
    """Kembalikan (capacity: int | None, charging: bool | None)."""
    status = SYSTEM_POWER_STATUS()
    ok = ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
    if not ok:
        return None, None
    cap = status.BatteryLifePercent
    if cap == 255:
        return None, None
    charging = status.ACLineStatus == 1
    print(f'[battery-alert] {cap}% | {"Charging" if charging else "Discharging"}', flush=True)
    return cap, charging


# ── Install / Startup ──────────────────────────────────────────────────────
def get_current_exe():
    """Dapatkan path exe saat ini (hanya valid saat frozen oleh PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return None  # running sebagai .py script

def is_running_from_install():
    exe = get_current_exe()
    if exe is None:
        return True  # skip install saat run sebagai script
    return os.path.normcase(exe) == os.path.normcase(INSTALL_PATH)

def install_and_run():
    """Salin exe ke AppData, set startup registry, lalu jalankan dari sana."""
    src = get_current_exe()
    if src is None:
        return  # tidak bisa self-install dari .py

    os.makedirs(INSTALL_DIR, exist_ok=True)

    # Salin exe ke install dir (skip jika sudah ada di path yang sama)
    if os.path.normcase(src) != os.path.normcase(INSTALL_PATH):
        shutil.copy2(src, INSTALL_PATH)

    # Daftarkan ke startup registry
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, REG_VALUE, 0, winreg.REG_SZ, INSTALL_PATH)
        winreg.CloseKey(key)
        print(f'[battery-alert] Startup registry set: {INSTALL_PATH}', flush=True)
    except Exception as e:
        print(f'[battery-alert] Registry error: {e}', flush=True)

    # Jalankan dari install path lalu keluar
    subprocess.Popen(
        [INSTALL_PATH, '--skip-install'],
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    )
    sys.exit(0)

def uninstall():
    """Hapus entry startup registry."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, REG_VALUE)
        winreg.CloseKey(key)
        print('[battery-alert] Startup registry dihapus.', flush=True)
    except FileNotFoundError:
        print('[battery-alert] Entry registry tidak ditemukan.', flush=True)
    except Exception as e:
        print(f'[battery-alert] Uninstall error: {e}', flush=True)


# ── Windows Acrylic blur (Windows 10 1803+ / Windows 11) ──────────────────
class _ACCENT_POLICY(Structure):
    _fields_ = [
        ('AccentState',  c_int),
        ('AccentFlags',  c_int),
        ('GradientColor',c_int),
        ('AnimationId',  c_int),
    ]

class _WINCOMP_ATTRIB_DATA(Structure):
    _fields_ = [
        ('Attribute',  c_int),
        ('Data',       POINTER(c_int)),
        ('SizeOfData', ctypes.c_size_t),
    ]

def apply_acrylic(hwnd: int, color_abgr: int = 0xC4040412):
    """Apply Windows Acrylic blur ke window handle."""
    try:
        accent = _ACCENT_POLICY()
        accent.AccentState   = 4       # ACCENT_ENABLE_ACRYLICBLURBEHIND
        accent.AccentFlags   = 2
        accent.GradientColor = color_abgr

        data = _WINCOMP_ATTRIB_DATA()
        data.Attribute  = 19           # WCA_ACCENT_POLICY
        data.SizeOfData = sizeof(accent)
        data.Data       = cast(pointer(accent), POINTER(c_int))

        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
    except Exception:
        pass  # fallback ke solid background jika API tidak tersedia


# ── Helper: rounded rectangle di canvas ───────────────────────────────────
def draw_rounded_rect(canvas, x1, y1, x2, y2, r=20, **kw):
    kw.setdefault('outline', '')
    pts = [
        x1+r, y1,   x2-r, y1,
        x2,   y1,   x2,   y1+r,
        x2,   y2-r, x2,   y2,
        x2-r, y2,   x1+r, y2,
        x1,   y2,   x1,   y2-r,
        x1,   y1+r, x1,   y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


# ── Alert Window (Toplevel) ────────────────────────────────────────────────
class AlertWindow:
    def __init__(self, root: tk.Tk, alert_type: str, capacity: int, on_closed_cb):
        self.root        = root
        self.alert_type  = alert_type
        self.capacity    = capacity
        self.on_closed   = on_closed_cb
        self._closed     = False
        self._tick       = 0
        self._icons_low  = ['🔋', '⚠️']
        self._icons_full = ['⚡', '🔌']

        self.win = tk.Toplevel(root)
        self._setup_window()
        self._build_ui()
        self._start_monitors()

    # ── Setup window ──────────────────────────────────────────────────────
    def _setup_window(self):
        w = self.win
        w.title('Battery Alert')
        w.overrideredirect(True)
        w.attributes('-topmost', True)
        w.attributes('-fullscreen', True)
        w.configure(bg='#04041a')
        w.attributes('-alpha', 0.97)

        sw = w.winfo_screenwidth()
        sh = w.winfo_screenheight()
        w.geometry(f'{sw}x{sh}+0+0')

        # Blokir semua keyboard input
        w.bind('<Key>', lambda e: 'break')
        w.protocol('WM_DELETE_WINDOW', lambda: None)

        # Acrylic blur setelah window muncul
        w.after(50, self._apply_blur)

    def _apply_blur(self):
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            apply_acrylic(hwnd, 0xC4040412)
        except Exception:
            pass

    # ── Build UI ──────────────────────────────────────────────────────────
    def _build_ui(self):
        is_low = self.alert_type == 'low'

        if is_low:
            card_bg    = '#150808'
            accent     = '#ff6e6e'
            bar_fill   = '#e03232'
            badge_text = 'BATERAI LEMAH'
            title_text = 'Baterai Hampir Habis!'
            msg_text   = 'Segera colokkan charger\nsebelum perangkat mati.'
            hint_text  = 'Notifikasi ini akan hilang saat charger terpasang'
            icons      = self._icons_low
        else:
            card_bg    = '#08150f'
            accent     = '#48ffa8'
            bar_fill   = '#28be6e'
            badge_text = 'BATERAI PENUH'
            title_text = 'Baterai Sudah Penuh!'
            msg_text   = 'Cabut charger untuk menjaga\nkesehatan baterai jangka panjang.'
            hint_text  = 'Notifikasi ini akan hilang saat charger dicabut'
            icons      = self._icons_full

        self._accent   = accent
        self._bar_fill = bar_fill
        self._icons    = icons

        # ── Canvas sebagai card ──
        CARD_W, CARD_H = 480, 440
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        cx = sw // 2 - CARD_W // 2
        cy = sh // 2 - CARD_H // 2

        self.canvas = tk.Canvas(
            self.win, width=sw, height=sh,
            bg='#04041a', highlightthickness=0
        )
        self.canvas.place(x=0, y=0)

        # Card background (rounded rect)
        draw_rounded_rect(
            self.canvas,
            cx, cy, cx + CARD_W, cy + CARD_H,
            r=28, fill=card_bg
        )
        # Card border
        draw_rounded_rect(
            self.canvas,
            cx, cy, cx + CARD_W, cy + CARD_H,
            r=28, fill='', outline=accent, width=1
        )
        # Shine line di atas card
        self.canvas.create_line(
            cx + 60, cy + 1, cx + CARD_W - 60, cy + 1,
            fill='#ffffff30', width=1
        )

        MID = cx + CARD_W // 2
        y   = cy + 52

        # Icon
        self.icon_id = self.canvas.create_text(
            MID, y, text=icons[0],
            font=('Segoe UI Emoji', 42), fill='white', anchor='n'
        )
        y += 68

        # Badge
        self.canvas.create_text(
            MID, y, text=badge_text,
            font=('Segoe UI', 10, 'bold'), fill=accent, anchor='n'
        )
        y += 30

        # Persen besar
        self.pct_id = self.canvas.create_text(
            MID - 12, y, text=str(self.capacity),
            font=('Segoe UI', 72, 'bold'), fill=accent, anchor='n'
        )
        self.canvas.create_text(
            MID + 34, y + 52, text='%',
            font=('Segoe UI', 16), fill='#ffffff55', anchor='s'
        )
        y += 90

        # Judul
        self.canvas.create_text(
            MID, y, text=title_text,
            font=('Segoe UI', 18, 'bold'), fill='#ffffffeb', anchor='n'
        )
        y += 36

        # Pesan
        self.canvas.create_text(
            MID, y, text=msg_text,
            font=('Segoe UI', 13), fill='#ffffff90', anchor='n', justify='center'
        )
        y += 56

        # Progress bar
        BAR_X1 = cx + 48
        BAR_X2 = cx + CARD_W - 48
        BAR_H  = 10
        self.canvas.create_rectangle(
            BAR_X1, y, BAR_X2, y + BAR_H,
            fill='#ffffff17', outline=''
        )
        bar_w = int((BAR_X2 - BAR_X1) * self.capacity / 100)
        self.bar_id = self.canvas.create_rectangle(
            BAR_X1, y, BAR_X1 + bar_w, y + BAR_H,
            fill=bar_fill, outline=''
        )
        self._bar_x1 = BAR_X1
        self._bar_x2 = BAR_X2
        self._bar_y1 = y
        self._bar_y2 = y + BAR_H
        y += 36

        # Divider
        self.canvas.create_line(
            cx + 48, y, cx + CARD_W - 48, y,
            fill='#ffffff17', width=1
        )
        y += 18

        # Hint
        self.canvas.create_text(
            MID, y, text=hint_text,
            font=('Segoe UI', 10, 'italic'), fill='#ffffff45', anchor='n'
        )

    # ── Update progress bar ───────────────────────────────────────────────
    def _update_bar(self):
        bar_w = int((self._bar_x2 - self._bar_x1) * self.capacity / 100)
        self.canvas.coords(
            self.bar_id,
            self._bar_x1, self._bar_y1,
            self._bar_x1 + bar_w, self._bar_y2
        )

    # ── Monitor & animasi ─────────────────────────────────────────────────
    def _start_monitors(self):
        self._schedule_check()
        self._animate()

    def _schedule_check(self):
        self.win.after(DISMISS_SEC * 1000, self._check_dismiss)

    def _check_dismiss(self):
        if self._closed:
            return

        cap, charging = read_battery()
        if cap is not None:
            self.capacity = cap
            self.canvas.itemconfig(self.pct_id, text=str(cap))
            self._update_bar()

        dismissed = (
            (self.alert_type == 'low'  and charging) or
            (self.alert_type == 'full' and not charging)
        )

        if dismissed:
            self._do_close()
        else:
            self._schedule_check()

    def _animate(self):
        if self._closed:
            return
        self._tick = (self._tick + 1) % 2
        self.canvas.itemconfig(self.icon_id, text=self._icons[self._tick])
        opacity = '#ffffff' if self._tick == 0 else '#ffffff80'
        self.canvas.itemconfig(self.icon_id, fill=opacity)
        self.win.after(900, self._animate)

    # ── Close ─────────────────────────────────────────────────────────────
    def _do_close(self):
        self._closed = True
        self.win.destroy()
        if self.on_closed:
            self.on_closed()


# ── Battery Monitor (background thread) ───────────────────────────────────
class BatteryMonitor:
    def __init__(self, root: tk.Tk):
        self.root          = root
        self._low_alerted  = False
        self._full_alerted = False
        self._alert_active = False

    def start(self):
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        time.sleep(2)  # tunggu UI siap
        self._check()
        while True:
            time.sleep(CHECK_SEC)
            self._check()

    def _check(self):
        if self._alert_active:
            return

        cap, charging = read_battery()
        if cap is None:
            return

        if cap <= THRESHOLD_LOW and not charging and not self._low_alerted:
            self._low_alerted  = True
            self._full_alerted = False
            self.root.after(0, lambda c=cap: self._show('low', c))
        elif cap > THRESHOLD_LOW + 5 or charging:
            self._low_alerted = False

        if cap >= THRESHOLD_FULL and charging and not self._full_alerted:
            self._full_alerted = True
            self._low_alerted  = False
            self.root.after(0, lambda c=cap: self._show('full', c))
        elif not charging or cap < THRESHOLD_FULL - 5:
            self._full_alerted = False

    def _show(self, alert_type: str, cap: int):
        self._alert_active = True
        AlertWindow(self.root, alert_type, cap, on_closed_cb=self._on_closed)

    def _on_closed(self):
        self._alert_active = False


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    args = sys.argv[1:]

    # ── Mode uninstall ──
    if '--uninstall' in args:
        uninstall()
        ctypes.windll.user32.MessageBoxW(
            0,
            'Battery Alert telah dihapus dari startup Windows.\n\n'
            'Hapus folder secara manual jika ingin membersihkan sepenuhnya:\n'
            f'{INSTALL_DIR}',
            'Battery Alert — Uninstall',
            0x40
        )
        sys.exit(0)

    # ── Mode test ──
    if '--test-low' in args or '--test-full' in args:
        alert_type = 'low' if '--test-low' in args else 'full'
        cap        = 15 if alert_type == 'low' else 95
        root = tk.Tk()
        root.withdraw()
        AlertWindow(root, alert_type, cap, on_closed_cb=root.quit)
        root.mainloop()
        sys.exit(0)

    # ── Install mode: jika belum di install path, install dulu ──
    if '--skip-install' not in args and not is_running_from_install():
        result = ctypes.windll.user32.MessageBoxW(
            0,
            'Battery Alert akan diinstall ke:\n'
            f'{INSTALL_DIR}\n\n'
            'App akan berjalan otomatis setiap Windows startup.\n\n'
            'Lanjutkan?',
            'Battery Alert — Installer',
            0x24  # MB_YESNO | MB_ICONQUESTION
        )
        if result == 6:  # IDYES
            install_and_run()
        sys.exit(0)

    # ── Run sebagai background monitor ──
    # Sembunyikan console window (saat frozen)
    if getattr(sys, 'frozen', False):
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )

    root = tk.Tk()
    root.withdraw()  # hidden root window

    monitor = BatteryMonitor(root)
    monitor.start()

    root.mainloop()
