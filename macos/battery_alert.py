#!/usr/bin/env python3
"""
Battery Alert — macOS
Glassmorphism-style popup saat baterai 20% (low) atau 90% saat dicas (full).
Popup hilang otomatis saat kondisi berubah.

Install mode: jalankan .app pertama kali untuk auto-install LaunchAgent (startup).
"""

import sys
import os
import re
import subprocess
import threading
import time

try:
    import tkinter as tk
except ImportError:
    sys.exit("ERROR: tkinter tidak tersedia. Install Python dari https://python.org")

# ── Konstanta ──────────────────────────────────────────────────────────────
THRESHOLD_LOW  = 20       # alert saat daya ≤ 20% (tidak dicas)
THRESHOLD_FULL = 90       # alert saat daya ≥ 90% (sedang dicas)
CHECK_SEC      = 30       # interval cek normal (detik)
DISMISS_SEC    = 5        # interval cek saat alert aktif (detik)

LABEL      = 'com.batteryalert'
PLIST_DIR  = os.path.expanduser('~/Library/LaunchAgents')
PLIST_PATH = os.path.join(PLIST_DIR, f'{LABEL}.plist')


# ── Baca baterai via pmset ─────────────────────────────────────────────────
def read_battery():
    """Kembalikan (capacity: int | None, charging: bool | None)."""
    try:
        out = subprocess.check_output(
            ['pmset', '-g', 'batt'], text=True, stderr=subprocess.DEVNULL
        )
        m = re.search(r'(\d+)%', out)
        if not m:
            return None, None
        cap      = int(m.group(1))
        charging = (
            'AC Power' in out or
            '; charging' in out or
            '; finishing charge' in out
        )
        print(f'[battery-alert] {cap}% | {"Charging" if charging else "Discharging"}', flush=True)
        return cap, charging
    except Exception as e:
        print(f'[battery-alert] ERROR read_battery: {e}', flush=True)
        return None, None


# ── LaunchAgent (startup) ──────────────────────────────────────────────────
def get_exe_path():
    """Path ke binary yang sedang berjalan."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(sys.argv[0])

def get_app_bundle():
    """Dapatkan path .app bundle (saat frozen oleh PyInstaller)."""
    exe = get_exe_path()
    # Struktur: BatteryAlert.app/Contents/MacOS/BatteryAlert
    macos_dir   = os.path.dirname(exe)
    contents    = os.path.dirname(macos_dir)
    app_path    = os.path.dirname(contents)
    if app_path.endswith('.app'):
        return app_path
    return None

def _plist_content(exe_path: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe_path}</string>
        <string>--skip-install</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/battery-alert.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/battery-alert.log</string>
</dict>
</plist>
"""

def install_launch_agent():
    """Tulis plist dan load ke launchctl."""
    exe = get_exe_path()
    os.makedirs(PLIST_DIR, exist_ok=True)
    with open(PLIST_PATH, 'w') as f:
        f.write(_plist_content(exe))
    # Unload dulu kalau sudah ada
    subprocess.run(['launchctl', 'unload', PLIST_PATH],
                   capture_output=True)
    subprocess.run(['launchctl', 'load', '-w', PLIST_PATH],
                   capture_output=True)
    print(f'[battery-alert] LaunchAgent terpasang: {PLIST_PATH}', flush=True)

def uninstall_launch_agent():
    """Unload dan hapus plist."""
    if os.path.exists(PLIST_PATH):
        subprocess.run(['launchctl', 'unload', PLIST_PATH], capture_output=True)
        os.remove(PLIST_PATH)
        print('[battery-alert] LaunchAgent dihapus.', flush=True)
    else:
        print('[battery-alert] LaunchAgent tidak ditemukan.', flush=True)

def is_launch_agent_installed() -> bool:
    return os.path.exists(PLIST_PATH)


# ── Helper: rounded rectangle di canvas ───────────────────────────────────
def draw_rounded_rect(canvas, x1, y1, x2, y2, r=24, **kw):
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
        w.configure(bg='#04041a')

        sw = w.winfo_screenwidth()
        sh = w.winfo_screenheight()

        # Fullscreen overlay
        w.overrideredirect(True)
        w.geometry(f'{sw}x{sh}+0+0')
        w.attributes('-topmost', True)

        # macOS: naikkan ke level paling atas via AppleScript (opsional)
        self._raise_window()

        # Blokir keyboard
        w.bind('<Key>', lambda e: 'break')
        w.protocol('WM_DELETE_WINDOW', lambda: None)

    def _raise_window(self):
        """Pastikan window di atas semua app lain di macOS."""
        try:
            self.win.tk.call(
                'wm', 'attributes', str(self.win),
                '-type', 'splash'
            )
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

        # Card background
        draw_rounded_rect(self.canvas, cx, cy, cx+CARD_W, cy+CARD_H,
                          r=28, fill=card_bg)
        draw_rounded_rect(self.canvas, cx, cy, cx+CARD_W, cy+CARD_H,
                          r=28, fill='', outline=accent, width=1)
        # Shine line
        self.canvas.create_line(cx+60, cy+1, cx+CARD_W-60, cy+1,
                                fill='#ffffff30', width=1)

        MID = cx + CARD_W // 2
        y   = cy + 52

        # Icon
        self.icon_id = self.canvas.create_text(
            MID, y, text=icons[0],
            font=('Apple Color Emoji', 42), fill='white', anchor='n'
        )
        y += 68

        # Badge
        self.canvas.create_text(
            MID, y, text=badge_text,
            font=('SF Pro Display', 10, 'bold'), fill=accent, anchor='n'
        )
        y += 30

        # Persen besar
        self.pct_id = self.canvas.create_text(
            MID - 12, y, text=str(self.capacity),
            font=('SF Pro Display', 72, 'bold'), fill=accent, anchor='n'
        )
        self.canvas.create_text(
            MID + 34, y + 52, text='%',
            font=('SF Pro Display', 16), fill='#ffffff55', anchor='s'
        )
        y += 90

        # Judul
        self.canvas.create_text(
            MID, y, text=title_text,
            font=('SF Pro Display', 18, 'bold'), fill='#ffffffeb', anchor='n'
        )
        y += 36

        # Pesan
        self.canvas.create_text(
            MID, y, text=msg_text,
            font=('SF Pro Display', 13), fill='#ffffff90',
            anchor='n', justify='center'
        )
        y += 56

        # Progress bar
        BAR_X1 = cx + 48
        BAR_X2 = cx + CARD_W - 48
        BAR_H  = 10
        self.canvas.create_rectangle(BAR_X1, y, BAR_X2, y+BAR_H,
                                     fill='#ffffff17', outline='')
        bar_w = int((BAR_X2 - BAR_X1) * self.capacity / 100)
        self.bar_id = self.canvas.create_rectangle(
            BAR_X1, y, BAR_X1 + bar_w, y + BAR_H,
            fill=bar_fill, outline=''
        )
        self._bar_x1, self._bar_x2 = BAR_X1, BAR_X2
        self._bar_y1, self._bar_y2 = y, y + BAR_H
        y += 36

        # Divider
        self.canvas.create_line(cx+48, y, cx+CARD_W-48, y,
                                fill='#ffffff17', width=1)
        y += 18

        # Hint
        self.canvas.create_text(
            MID, y, text=hint_text,
            font=('SF Pro Display', 10, 'italic'), fill='#ffffff45', anchor='n'
        )

    def _update_bar(self):
        bar_w = int((self._bar_x2 - self._bar_x1) * self.capacity / 100)
        self.canvas.coords(
            self.bar_id,
            self._bar_x1, self._bar_y1,
            self._bar_x1 + bar_w, self._bar_y2
        )

    # ── Monitor & animasi ─────────────────────────────────────────────────
    def _start_monitors(self):
        self.win.after(DISMISS_SEC * 1000, self._check_dismiss)
        self._animate()

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
            self.win.after(DISMISS_SEC * 1000, self._check_dismiss)

    def _animate(self):
        if self._closed:
            return
        self._tick = (self._tick + 1) % 2
        self.canvas.itemconfig(self.icon_id, text=self._icons[self._tick])
        self.canvas.itemconfig(
            self.icon_id,
            fill='#ffffff' if self._tick == 0 else '#ffffff80'
        )
        self.win.after(900, self._animate)

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
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        time.sleep(2)
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


# ── Dialog installer (native macOS via osascript) ─────────────────────────
def macos_dialog(title: str, msg: str, buttons=('Batal', 'Ya'),
                 default_button='Ya') -> str:
    """Tampilkan dialog native macOS. Kembalikan teks tombol yang diklik."""
    btn_str = ', '.join(f'"{b}"' for b in buttons)
    script  = (
        f'tell app "System Events" to display dialog "{msg}" '
        f'with title "{title}" '
        f'buttons {{{btn_str}}} '
        f'default button "{default_button}"'
    )
    result = subprocess.run(
        ['osascript', '-e', script],
        capture_output=True, text=True
    )
    out = result.stdout.strip()
    # Output: "button returned:Ya"
    if 'button returned:' in out:
        return out.split('button returned:')[-1].strip()
    return ''


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    args = sys.argv[1:]

    # ── Mode uninstall ──
    if '--uninstall' in args:
        uninstall_launch_agent()
        macos_dialog(
            'Battery Alert — Uninstall',
            'Battery Alert telah dihapus dari startup macOS.\n\n'
            'Kamu bisa hapus BatteryAlert.app dari Applications secara manual.',
            buttons=('OK',), default_button='OK'
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

    # ── Install mode ──
    if '--skip-install' not in args and not is_launch_agent_installed():
        clicked = macos_dialog(
            'Battery Alert — Installer',
            'Battery Alert akan dipasang sebagai startup item.\n\n'
            'App akan berjalan otomatis setiap kamu login ke macOS.\n\n'
            'Lanjutkan?'
        )
        if clicked == 'Ya':
            install_launch_agent()
            macos_dialog(
                'Battery Alert',
                'Berhasil dipasang!\n\n'
                'Battery Alert akan berjalan otomatis saat login.\n'
                'Sekarang mulai memantau baterai...',
                buttons=('OK',), default_button='OK'
            )
        else:
            sys.exit(0)

    # ── Run sebagai background monitor ──
    root = tk.Tk()
    root.withdraw()

    monitor = BatteryMonitor(root)
    monitor.start()

    root.mainloop()
