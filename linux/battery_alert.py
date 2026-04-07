#!/usr/bin/env python3
"""
Battery Alert — Linux GTK4
Glassmorphism popup saat baterai 20% (low) atau 90% saat dicas (full).
Popup tidak bisa ditutup manual; hilang otomatis saat kondisi berubah.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')

from gi.repository import Gtk, Gdk, GLib, Gio
import os, sys, math

# ── Battery path detection ────────────────────────────────────────────────────
BATTERY_PATH = None
for _b in ['BAT0', 'BAT1', 'BAT2', 'battery']:
    _p = f'/sys/class/power_supply/{_b}'
    if os.path.exists(_p):
        BATTERY_PATH = _p
        break

THRESHOLD_LOW  = 20   # alert saat daya ≤ 20% (tidak dicas)
THRESHOLD_FULL = 90   # alert saat daya ≥ 90% (sedang dicas)
CHECK_MS       = 30_000  # interval cek normal (ms)
DISMISS_MS     = 5_000   # interval cek saat alert aktif (ms)

# ── CSS Glassmorphism ─────────────────────────────────────────────────────────
CSS = """
/* ── Overlay gelap ── */
window.alert-overlay {
    background-color: rgba(4, 4, 18, 0.78);
}

/* ── Kartu kaca ── */
.glass-card {
    background: linear-gradient(
        145deg,
        rgba(255, 255, 255, 0.13) 0%,
        rgba(255, 255, 255, 0.05) 45%,
        rgba(120, 160, 255, 0.07) 100%
    );
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 28px;
    padding: 52px 60px 44px 60px;
    min-width: 440px;
    box-shadow:
        0 0 0 1px rgba(255,255,255,0.04) inset,
        0 8px 48px rgba(0,0,0,0.55),
        0 2px 8px  rgba(0,0,0,0.35);
}

.glass-card.low-battery {
    border-color: rgba(255, 90, 90, 0.30);
    background: linear-gradient(
        145deg,
        rgba(255, 70, 70, 0.13) 0%,
        rgba(255, 255, 255, 0.04) 45%,
        rgba(200, 40, 40, 0.08) 100%
    );
    box-shadow:
        0 0 0 1px rgba(255,100,100,0.08) inset,
        0 0 60px rgba(255, 60, 60, 0.18),
        0 8px 48px rgba(0,0,0,0.55);
}

.glass-card.full-battery {
    border-color: rgba(72, 255, 168, 0.30);
    background: linear-gradient(
        145deg,
        rgba(60, 220, 140, 0.12) 0%,
        rgba(255, 255, 255, 0.04) 45%,
        rgba(40, 180, 110, 0.08) 100%
    );
    box-shadow:
        0 0 0 1px rgba(72,255,168,0.08) inset,
        0 0 60px rgba(60, 220, 140, 0.16),
        0 8px 48px rgba(0,0,0,0.55);
}

/* ── Inner shine line di bagian atas kartu ── */
.glass-card .shine {
    background: linear-gradient(
        90deg,
        transparent,
        rgba(255,255,255,0.18) 50%,
        transparent
    );
    min-height: 1px;
    border-radius: 2px;
    margin-bottom: 32px;
}

/* ── Ikon besar ── */
.icon-label {
    font-size: 60px;
    margin-bottom: 4px;
}

/* ── Badge tipe alert ── */
.badge {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 20px;
    padding: 4px 16px;
    margin-bottom: 24px;
}

.badge label {
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    color: rgba(255, 255, 255, 0.55);
}

.badge.low label  { color: rgba(255, 130, 130, 0.80); }
.badge.full label { color: rgba(80,  255, 168, 0.80); }

/* ── Angka persen besar ── */
.percent-label {
    font-size: 72px;
    font-weight: bold;
    color: rgba(255, 255, 255, 0.96);
    margin-bottom: 0px;
}
.percent-label.low  { color: rgba(255, 110, 110, 0.98); }
.percent-label.full { color: rgba(80,  255, 160, 0.98); }

/* ── Unit label ── */
.unit-label {
    font-size: 16px;
    color: rgba(255,255,255,0.35);
    margin-bottom: 20px;
}

/* ── Judul ── */
.title-label {
    font-size: 18px;
    font-weight: bold;
    color: rgba(255, 255, 255, 0.92);
    margin-bottom: 8px;
}

/* ── Pesan ── */
.message-label {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.58);
    margin-bottom: 32px;
}

/* ── Progress bar ── */
progressbar.battery-bar {
    margin-bottom: 32px;
}
progressbar.battery-bar trough {
    background-color: rgba(255, 255, 255, 0.09);
    border-radius: 10px;
    min-height: 10px;
    border: none;
    box-shadow: none;
}
progressbar.battery-bar.low trough progress {
    background: linear-gradient(90deg, rgba(220,50,50,0.92), rgba(255,130,50,0.92));
    border-radius: 10px;
    border: none;
    box-shadow: 0 0 10px rgba(255,80,50,0.35);
}
progressbar.battery-bar.full trough progress {
    background: linear-gradient(90deg, rgba(40,190,110,0.92), rgba(80,255,168,0.92));
    border-radius: 10px;
    border: none;
    box-shadow: 0 0 10px rgba(60,220,140,0.35);
}

/* ── Divider ── */
.divider {
    background: rgba(255,255,255,0.07);
    min-height: 1px;
    margin-bottom: 20px;
}

/* ── Hint kecil di bawah ── */
.hint-label {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.28);
    font-style: italic;
}

/* ── Animasi pulse (toggle class) ── */
.pulse-on  { opacity: 1.0; }
.pulse-off { opacity: 0.5; }
"""


# ── Baca info baterai ─────────────────────────────────────────────────────────
def read_battery():
    """Kembalikan (capacity: int | None, status: str | None).

    Persentase dihitung dari charge_now/charge_full (sama dengan upower/GNOME),
    bukan dari /capacity yang memakai charge_full_design (kapasitas desain awal).
    Ini penting karena baterai yang sudah terpakai banyak siklus akan melaporkan
    angka berbeda antara dua metode tersebut.
    """
    if not BATTERY_PATH:
        return None, None
    try:
        status = open(f'{BATTERY_PATH}/status').read().strip()

        # Prioritas: charge_now / charge_full (akurat, sama dengan GNOME/upower)
        charge_now_path  = f'{BATTERY_PATH}/charge_now'
        charge_full_path = f'{BATTERY_PATH}/charge_full'
        if os.path.exists(charge_now_path) and os.path.exists(charge_full_path):
            now  = int(open(charge_now_path).read().strip())
            full = int(open(charge_full_path).read().strip())
            cap  = round(now / full * 100) if full > 0 else 0
        else:
            # Fallback: energy_now / energy_full
            e_now_path  = f'{BATTERY_PATH}/energy_now'
            e_full_path = f'{BATTERY_PATH}/energy_full'
            if os.path.exists(e_now_path) and os.path.exists(e_full_path):
                now  = int(open(e_now_path).read().strip())
                full = int(open(e_full_path).read().strip())
                cap  = round(now / full * 100) if full > 0 else 0
            else:
                # Fallback terakhir: /capacity
                cap = int(open(f'{BATTERY_PATH}/capacity').read().strip())

        print(f'[battery-alert] {cap}% | {status}', flush=True)
        return cap, status
    except Exception as e:
        print(f'[battery-alert] ERROR read_battery: {e}', flush=True)
        return None, None


# ── Jendela Alert ─────────────────────────────────────────────────────────────
class AlertWindow(Gtk.Window):
    def __init__(self, app, alert_type: str, capacity: int):
        super().__init__(application=app)
        self.alert_type  = alert_type   # 'low' | 'full'
        self.capacity    = capacity
        self._closed     = False
        self._tick       = 0
        self._icons_low  = ['🔋', '⚠️']
        self._icons_full = ['⚡', '🔌']

        self._setup_window()
        self._build_ui()
        self._start_monitors()

    # ── Setup window ──────────────────────────────────────────────────────────
    def _setup_window(self):
        self.set_title("Battery Alert")
        self.set_decorated(False)
        self.set_resizable(False)
        self.add_css_class('alert-overlay')

        # Fullscreen agar mentutupi seluruh layar
        display = Gdk.Display.get_default()
        w, h = 1920, 1080
        if display:
            mon = display.get_monitors().get_item(0)
            if mon:
                geo = mon.get_geometry()
                w, h = geo.width, geo.height
        self.set_default_size(w, h)

        # Blokir penutupan manual
        self.connect('close-request', self._on_close_request)

        # Blokir tombol keyboard (Esc, Alt+F4 dll.)
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect('key-pressed', self._block_keys)
        self.add_controller(key_ctrl)

    # ── Bangun UI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        is_low = self.alert_type == 'low'

        # ── Pusat ──
        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        center.set_halign(Gtk.Align.CENTER)
        center.set_valign(Gtk.Align.CENTER)

        # ── Kartu kaca ──
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        card.set_halign(Gtk.Align.CENTER)
        card.add_css_class('glass-card')
        card.add_css_class('low-battery' if is_low else 'full-battery')

        # Shine line
        shine = Gtk.Box()
        shine.add_css_class('shine')
        card.append(shine)

        # Ikon
        self.icon_lbl = Gtk.Label(label='🔋' if is_low else '⚡')
        self.icon_lbl.set_halign(Gtk.Align.CENTER)
        self.icon_lbl.add_css_class('icon-label')
        self.icon_lbl.add_css_class('pulse-on')
        card.append(self.icon_lbl)

        # Badge
        badge_box = Gtk.Box()
        badge_box.set_halign(Gtk.Align.CENTER)
        badge_box.add_css_class('badge')
        badge_box.add_css_class('low' if is_low else 'full')
        badge_lbl = Gtk.Label(label='BATERAI LEMAH' if is_low else 'BATERAI PENUH')
        badge_box.append(badge_lbl)
        card.append(badge_box)

        # Persen besar
        pct_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        pct_row.set_halign(Gtk.Align.CENTER)

        self.pct_lbl = Gtk.Label(label=str(self.capacity))
        self.pct_lbl.add_css_class('percent-label')
        self.pct_lbl.add_css_class('low' if is_low else 'full')
        pct_row.append(self.pct_lbl)

        unit = Gtk.Label(label='%')
        unit.add_css_class('unit-label')
        unit.set_valign(Gtk.Align.END)
        unit.set_margin_bottom(14)
        pct_row.append(unit)
        card.append(pct_row)

        # Judul
        title = Gtk.Label(
            label='Baterai Hampir Habis!' if is_low else 'Baterai Sudah Penuh!'
        )
        title.set_halign(Gtk.Align.CENTER)
        title.add_css_class('title-label')
        card.append(title)

        # Pesan
        msg_text = (
            'Segera colokkan charger\nsebelum perangkat mati.'
            if is_low else
            'Cabut charger untuk menjaga\nkesehatan baterai jangka panjang.'
        )
        msg = Gtk.Label(label=msg_text)
        msg.set_halign(Gtk.Align.CENTER)
        msg.set_justify(Gtk.Justification.CENTER)
        msg.add_css_class('message-label')
        card.append(msg)

        # Progress bar
        self.pbar = Gtk.ProgressBar()
        self.pbar.set_fraction(self.capacity / 100)
        self.pbar.set_hexpand(True)
        self.pbar.add_css_class('battery-bar')
        self.pbar.add_css_class('low' if is_low else 'full')
        card.append(self.pbar)

        # Divider
        div = Gtk.Box()
        div.add_css_class('divider')
        card.append(div)

        # Hint
        hint_text = (
            'Notifikasi ini akan hilang saat charger terpasang'
            if is_low else
            'Notifikasi ini akan hilang saat charger dicabut'
        )
        hint = Gtk.Label(label=hint_text)
        hint.set_halign(Gtk.Align.CENTER)
        hint.add_css_class('hint-label')
        card.append(hint)

        center.append(card)
        self.set_child(center)

    # ── Monitor & animasi ─────────────────────────────────────────────────────
    def _start_monitors(self):
        GLib.timeout_add(DISMISS_MS,  self._check_dismiss)
        GLib.timeout_add(900, self._animate)

    def _check_dismiss(self):
        if self._closed:
            return False

        cap, status = read_battery()
        charging = status in ('Charging', 'Full')

        # Update tampilan
        if cap is not None:
            self.capacity = cap
            self.pct_lbl.set_label(str(cap))
            self.pbar.set_fraction(cap / 100)

        # Kondisi dismiss otomatis
        if self.alert_type == 'low'  and charging:
            self._do_close(); return False
        if self.alert_type == 'full' and not charging:
            self._do_close(); return False

        return True

    def _animate(self):
        if self._closed:
            return False
        self._tick = (self._tick + 1) % 2

        is_low = self.alert_type == 'low'
        icons  = self._icons_low if is_low else self._icons_full
        self.icon_lbl.set_label(icons[self._tick])

        if self._tick == 0:
            self.icon_lbl.remove_css_class('pulse-off')
            self.icon_lbl.add_css_class('pulse-on')
        else:
            self.icon_lbl.remove_css_class('pulse-on')
            self.icon_lbl.add_css_class('pulse-off')

        return True

    # ── Event handlers ────────────────────────────────────────────────────────
    def _on_close_request(self, _win):
        cap, status = read_battery()
        charging = status in ('Charging', 'Full')

        if self.alert_type == 'low'  and not charging: return True  # blokir
        if self.alert_type == 'full' and charging:     return True  # blokir

        self._closed = True
        return False

    def _block_keys(self, _ctrl, keyval, _code, _state):
        # Izinkan hanya jika kondisi sudah berubah (dismiss_check akan handle)
        return True  # telan semua keypress

    def _do_close(self):
        self._closed = True
        self.close()


# ── Aplikasi utama ────────────────────────────────────────────────────────────
class BatteryAlertApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id='id.batteryalert.monitor',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self._win            = None
        self._low_alerted    = False
        self._full_alerted   = False
    def do_activate(self):
        self._apply_css()
        self.hold()  # jaga proses tetap hidup walau tanpa window

        # _TEST_TYPE di-set di entry point sebelum app.run() dipanggil
        test = globals().get('_TEST_TYPE')
        if test == 'low':
            self._show_alert('low', 15)
        elif test == 'full':
            self._show_alert('full', 95)
        else:
            # Cek sekali langsung, lalu jadwalkan berkala
            GLib.timeout_add(1000, self._initial_check)
            GLib.timeout_add(CHECK_MS, self._periodic_check)

    # ── CSS ───────────────────────────────────────────────────────────────────
    def _apply_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # ── Cek baterai ───────────────────────────────────────────────────────────
    def _initial_check(self):
        self._do_check()
        return False  # hanya sekali

    def _periodic_check(self):
        self._do_check()
        return True  # ulangi terus

    def _do_check(self):
        cap, status = read_battery()
        if cap is None:
            return

        charging = status in ('Charging', 'Full')

        # ── Low battery ───────────────────────────────────────────────────────
        if cap <= THRESHOLD_LOW and not charging:
            if not self._low_alerted:
                self._low_alerted  = True
                self._full_alerted = False
                self._show_alert('low', cap)
        elif cap > THRESHOLD_LOW + 5 or charging:
            self._low_alerted = False

        # ── Full battery ──────────────────────────────────────────────────────
        if cap >= THRESHOLD_FULL and charging:
            if not self._full_alerted:
                self._full_alerted = True
                self._low_alerted  = False
                self._show_alert('full', cap)
        elif not charging or cap < THRESHOLD_FULL - 5:
            self._full_alerted = False

    # ── Tampilkan alert ───────────────────────────────────────────────────────
    def _show_alert(self, alert_type: str, capacity: int):
        # Tutup window lama jika ada
        if self._win and not self._win._closed:
            self._win._closed = True
            self._win.close()

        self._win = AlertWindow(self, alert_type, capacity)
        self._win.present()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if BATTERY_PATH is None:
        print("ERROR: Tidak ada baterai yang terdeteksi di /sys/class/power_supply/")
        sys.exit(1)

    # Simpan flag test sebelum GTK parse argv (GTK tidak kenal flag custom)
    _TEST_TYPE = (
        'low'  if '--test-low'  in sys.argv else
        'full' if '--test-full' in sys.argv else
        None
    )

    app = BatteryAlertApp()
    # Hanya pass nama program; argumen custom sudah disimpan di _TEST_TYPE
    sys.exit(app.run(sys.argv[:1]))
