#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""RetroDualStation Kontrollcenter – Prototyp 0.3

Zeigt auf dem unteren Bildschirm (DSI-1) eine Fläche auf der Wayland-Overlay-Ebene,
also über ES und über jedem Emulator.

  Anbernic-Taste (allein gedrückt)  -> Kontrollcenter ein/aus
  Return/Home-Taste                 -> Gameswitcher (Platzhalter) ein/aus
  B                                 -> schließen
  L1 / R1, Wischen                  -> Seite wechseln
  Steuerkreuz, A, Touch             -> bedienen

Nur Python 3 + libwayland-client + libcairo (beides auf ROCKNIX vorhanden).
Start zum Testen über SSH:   python3 rds_cc.py      (Ende mit Strg+C)

Einstellungen (optional): /storage/.config/retrodualstation/controlcenter.json
  {"theme": "dark" | "light", "accent": "#e5383b",
   "backlight_top": "<name>", "backlight_bottom": "<name>"}
"""
import ctypes
import fcntl
import glob
import json
import mmap
import os
import re
import select
import shutil
import struct
import subprocess
import sys
import time
from ctypes import (CDLL, CFUNCTYPE, POINTER, Structure, Union, byref, c_char,
                    c_char_p, c_double, c_int, c_int32, c_uint32, c_void_p, cast,
                    pointer)

VERSION = "0.3"
OUTPUT_NAME = os.environ.get("RDS_CC_OUTPUT", "DSI-1")
JOYPAD_NAME = os.environ.get("RDS_CC_JOYPAD", "retrogame_joypad")
HOME_NAME = os.environ.get("RDS_CC_HOMEKEY", "adc-keys-back")
CONFIG_PATH = "/storage/.config/retrodualstation/controlcenter.json"
os.environ.setdefault("XDG_RUNTIME_DIR", "/var/run/0-runtime-dir")
os.environ.setdefault("WAYLAND_DISPLAY", "wayland-1")


def log(*a):
    print("[rds-cc]", *a, flush=True)


# ---------------------------------------------------------------- Wayland ----

wl = CDLL("libwayland-client.so.0")


class WlInterface(Structure):
    pass


class WlMessage(Structure):
    _fields_ = [("name", c_char_p), ("signature", c_char_p),
                ("types", POINTER(POINTER(WlInterface)))]


WlInterface._fields_ = [("name", c_char_p), ("version", c_int),
                        ("method_count", c_int), ("methods", POINTER(WlMessage)),
                        ("event_count", c_int), ("events", POINTER(WlMessage))]


class WlArgument(Union):
    _fields_ = [("i", c_int32), ("u", c_uint32), ("s", c_char_p), ("o", c_void_p),
                ("h", c_int32)]


wl.wl_display_connect.restype = c_void_p
wl.wl_display_connect.argtypes = [c_char_p]
for _fn in ("wl_display_roundtrip", "wl_display_dispatch_pending", "wl_display_flush",
            "wl_display_prepare_read", "wl_display_read_events", "wl_display_get_fd"):
    getattr(wl, _fn).restype = c_int
    getattr(wl, _fn).argtypes = [c_void_p]
wl.wl_display_cancel_read.restype = None
wl.wl_display_cancel_read.argtypes = [c_void_p]
wl.wl_proxy_marshal_array_flags.restype = c_void_p
wl.wl_proxy_marshal_array_flags.argtypes = [c_void_p, c_uint32, POINTER(WlInterface),
                                            c_uint32, c_uint32, POINTER(WlArgument)]
wl.wl_proxy_add_listener.restype = c_int
wl.wl_proxy_add_listener.argtypes = [c_void_p, c_void_p, c_void_p]
wl.wl_proxy_get_version.restype = c_uint32
wl.wl_proxy_get_version.argtypes = [c_void_p]


def core(name):
    return WlInterface.in_dll(wl, name)


IF_REGISTRY = core("wl_registry_interface")
IF_COMPOSITOR = core("wl_compositor_interface")
IF_SURFACE = core("wl_surface_interface")
IF_SHM = core("wl_shm_interface")
IF_SHM_POOL = core("wl_shm_pool_interface")
IF_BUFFER = core("wl_buffer_interface")
IF_OUTPUT = core("wl_output_interface")
IF_SEAT = core("wl_seat_interface")
IF_TOUCH = core("wl_touch_interface")

_keep = []  # hält ctypes-Objekte am Leben


def _types(*ifaces):
    arr = (POINTER(WlInterface) * max(1, len(ifaces)))()
    for i, iface in enumerate(ifaces):
        arr[i] = pointer(iface) if iface is not None else POINTER(WlInterface)()
    _keep.append(arr)
    return cast(arr, POINTER(POINTER(WlInterface)))


def _messages(specs):
    arr = (WlMessage * len(specs))()
    for i, (name, sig, types) in enumerate(specs):
        arr[i].name = name
        arr[i].signature = sig
        arr[i].types = types
    _keep.append(arr)
    return arr


# wlr-layer-shell-unstable-v1 (nur das Protokoll, keine fremde Implementierung)
IF_LAYER_SHELL = WlInterface()
IF_LAYER_SURFACE = WlInterface()
_n = None
_ls_methods = _messages([
    (b"set_size", b"uu", _types(_n, _n)),
    (b"set_anchor", b"u", _types(_n)),
    (b"set_exclusive_zone", b"i", _types(_n)),
    (b"set_margin", b"iiii", _types(_n, _n, _n, _n)),
    (b"set_keyboard_interactivity", b"u", _types(_n)),
    (b"get_popup", b"o", _types(_n)),
    (b"ack_configure", b"u", _types(_n)),
    (b"destroy", b"", _types()),
    (b"set_layer", b"2u", _types(_n)),
])
_ls_events = _messages([
    (b"configure", b"uuu", _types(_n, _n, _n)),
    (b"closed", b"", _types()),
])
IF_LAYER_SURFACE.name = b"zwlr_layer_surface_v1"
IF_LAYER_SURFACE.version = 4
IF_LAYER_SURFACE.method_count = 9
IF_LAYER_SURFACE.methods = _ls_methods
IF_LAYER_SURFACE.event_count = 2
IF_LAYER_SURFACE.events = _ls_events
_shell_methods = _messages([
    (b"get_layer_surface", b"no?ous", _types(IF_LAYER_SURFACE, IF_SURFACE, IF_OUTPUT, _n, _n)),
    (b"destroy", b"3", _types()),
])
IF_LAYER_SHELL.name = b"zwlr_layer_shell_v1"
IF_LAYER_SHELL.version = 4
IF_LAYER_SHELL.method_count = 2
IF_LAYER_SHELL.methods = _shell_methods
IF_LAYER_SHELL.event_count = 0
IF_LAYER_SHELL.events = cast(None, POINTER(WlMessage))

LAYER_OVERLAY = 3
ANCHOR_ALL = 1 | 2 | 4 | 8
SEAT_CAP_TOUCH = 4


def marshal(proxy, opcode, new_iface=None, *args, destroy=False, version=None):
    """args: Tupel (typ, wert) mit typ in u/i/s/o/n/h."""
    arr = (WlArgument * max(1, len(args)))()
    keep = []
    for i, (kind, val) in enumerate(args):
        if kind == "u":
            arr[i].u = val
        elif kind == "i":
            arr[i].i = val
        elif kind == "h":
            arr[i].h = val
        elif kind == "s":
            keep.append(val)
            arr[i].s = val
        elif kind in ("o", "n"):
            arr[i].o = val
    if version is None:
        version = wl.wl_proxy_get_version(proxy)
    return wl.wl_proxy_marshal_array_flags(
        proxy, opcode, byref(new_iface) if new_iface is not None else None,
        version, 1 if destroy else 0, arr)


def listen(proxy, *callbacks):
    impl = (c_void_p * len(callbacks))(*[cast(cb, c_void_p) for cb in callbacks])
    _keep.extend(callbacks)
    _keep.append(impl)
    wl.wl_proxy_add_listener(proxy, impl, None)


def safe(fn):
    """Wayland-Callbacks dürfen nie eine Ausnahme werfen."""
    def wrapper(*a):
        try:
            fn(*a)
        except Exception as exc:
            log("Fehler in", fn.__name__ + ":", exc)
    wrapper.__name__ = fn.__name__
    return wrapper


# ------------------------------------------------------------------ Cairo ----

cairo = CDLL("libcairo.so.2")
cairo.cairo_image_surface_create_for_data.restype = c_void_p
cairo.cairo_image_surface_create_for_data.argtypes = [c_void_p, c_int, c_int, c_int, c_int]
cairo.cairo_create.restype = c_void_p
cairo.cairo_create.argtypes = [c_void_p]
for _fn, _args in {
    "cairo_set_source_rgba": [c_void_p, c_double, c_double, c_double, c_double],
    "cairo_rectangle": [c_void_p, c_double, c_double, c_double, c_double],
    "cairo_arc": [c_void_p, c_double, c_double, c_double, c_double, c_double],
    "cairo_new_sub_path": [c_void_p], "cairo_close_path": [c_void_p],
    "cairo_new_path": [c_void_p],
    "cairo_fill": [c_void_p], "cairo_paint": [c_void_p], "cairo_stroke": [c_void_p],
    "cairo_set_line_width": [c_void_p, c_double],
    "cairo_select_font_face": [c_void_p, c_char_p, c_int, c_int],
    "cairo_set_font_size": [c_void_p, c_double],
    "cairo_move_to": [c_void_p, c_double, c_double],
    "cairo_show_text": [c_void_p, c_char_p],
    "cairo_surface_flush": [c_void_p], "cairo_destroy": [c_void_p],
    "cairo_surface_destroy": [c_void_p],
}.items():
    getattr(cairo, _fn).restype = None
    getattr(cairo, _fn).argtypes = _args


class TextExtents(Structure):
    _fields_ = [(n, c_double) for n in ("x_bearing", "y_bearing", "width", "height",
                                        "x_advance", "y_advance")]


cairo.cairo_text_extents.restype = None
cairo.cairo_text_extents.argtypes = [c_void_p, c_char_p, POINTER(TextExtents)]

PI = 3.141592653589793


def _rgb(hexstr, a=1.0):
    h = hexstr.lstrip("#")
    return int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a


class Pen:
    """Zeichnet in Entwurfs-Koordinaten (Entwurf 1260 × 951) und skaliert aufs Display."""

    def __init__(self, cr, w, h):
        self.cr, self.w, self.h = cr, w, h
        self.s = min(w / 1260, h / 951)
        self.ox = (w - 1260 * self.s) / 2
        self.oy = (h - 951 * self.s) / 2

    def X(self, x):
        return self.ox + x * self.s

    def Y(self, y):
        return self.oy + y * self.s

    def color(self, c, a=1.0):
        cairo.cairo_set_source_rgba(self.cr, *_rgb(c, a))

    def fill_all(self, c):
        self.color(c)
        cairo.cairo_paint(self.cr)

    def rrect(self, x, y, w, h, r, c, a=1.0, stroke=0):
        cr, s = self.cr, self.s
        x, y, w, h, r = self.X(x), self.Y(y), w * s, h * s, min(r * s, h * s / 2, w * s / 2)
        cairo.cairo_new_path(cr)
        cairo.cairo_new_sub_path(cr)
        cairo.cairo_arc(cr, x + w - r, y + r, r, -PI / 2, 0)
        cairo.cairo_arc(cr, x + w - r, y + h - r, r, 0, PI / 2)
        cairo.cairo_arc(cr, x + r, y + h - r, r, PI / 2, PI)
        cairo.cairo_arc(cr, x + r, y + r, r, PI, 3 * PI / 2)
        cairo.cairo_close_path(cr)
        self.color(c, a)
        if stroke:
            cairo.cairo_set_line_width(cr, stroke * s)
            cairo.cairo_stroke(cr)
        else:
            cairo.cairo_fill(cr)

    def circle(self, x, y, r, c):
        cairo.cairo_new_path(self.cr)
        cairo.cairo_arc(self.cr, self.X(x), self.Y(y), r * self.s, 0, 2 * PI)
        self.color(c)
        cairo.cairo_fill(self.cr)

    def text(self, txt, size, x, y, c, bold=False, align="l"):
        cr = self.cr
        cairo.cairo_select_font_face(cr, b"sans-serif", 0, 1 if bold else 0)
        cairo.cairo_set_font_size(cr, size * self.s)
        data = txt.encode("utf-8")
        ext = TextExtents()
        cairo.cairo_text_extents(cr, data, byref(ext))
        px = self.X(x)
        if align == "c":
            px -= ext.x_advance / 2
        elif align == "r":
            px -= ext.x_advance
        self.color(c)
        cairo.cairo_move_to(cr, px, self.Y(y))
        cairo.cairo_show_text(cr, data)
        return ext.x_advance / self.s

    def width(self, txt, size, bold=False):
        cairo.cairo_select_font_face(self.cr, b"sans-serif", 0, 1 if bold else 0)
        cairo.cairo_set_font_size(self.cr, size * self.s)
        ext = TextExtents()
        cairo.cairo_text_extents(self.cr, txt.encode("utf-8"), byref(ext))
        return ext.x_advance / self.s

    def to_design(self, px, py):
        return (px - self.ox) / self.s, (py - self.oy) / self.s


# ------------------------------------------------------------ System ---------

def run(cmd, timeout=2.0):
    if not shutil.which(cmd[0]):
        return None
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def spawn(cmd):
    """Befehl im Hintergrund starten, ohne auf ihn zu warten."""
    if not shutil.which(cmd[0]):
        log("Befehl nicht vorhanden:", cmd[0])
        return False
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError as exc:
        log("Start fehlgeschlagen:", cmd, exc)
        return False


def rd(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def wr(path, val):
    try:
        with open(path, "w") as f:
            f.write(str(val))
        return True
    except OSError as exc:
        log("Schreiben fehlgeschlagen:", path, exc)
        return False


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


class Backlight:
    def __init__(self, name):
        self.name = name
        self.dir = "/sys/class/backlight/" + name
        try:
            self.max = int(rd(self.dir + "/max_brightness") or 0) or 255
        except ValueError:
            self.max = 255

    def get(self):
        v = rd(self.dir + "/brightness")
        return round(int(v) * 100 / self.max) if v and v.isdigit() else 50

    def set(self, pct):
        wr(self.dir + "/brightness", max(1, round(max(5, min(100, pct)) * self.max / 100)))


def find_backlights(cfg):
    names = sorted(os.path.basename(p) for p in glob.glob("/sys/class/backlight/*"))
    for n in names:
        log("Hintergrundbeleuchtung:", n, "->", os.path.realpath("/sys/class/backlight/" + n))
    # RG DS Plus: backlight1 = oben, backlight0 = unten (getestet 19.10.2026)
    top = cfg.get("backlight_top") or (names[-1] if names else None)
    bottom = cfg.get("backlight_bottom") or next((n for n in names if n != top), None)
    result = []
    if top in names:
        result.append(("Helligkeit oben", Backlight(top)))
    if bottom in names:
        result.append(("Helligkeit unten", Backlight(bottom)))
    return result


def volume_get():
    out = run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
    m = re.search(r"([\d.]+)", out or "")
    return min(100, round(float(m.group(1)) * 100)) if m else None


def volume_set(pct):
    spawn(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "%.2f" % (max(0, min(100, pct)) / 100)])


CPU_GOV = sorted(glob.glob("/sys/devices/system/cpu/cpufreq/policy*/scaling_governor"))
GPU_GOV = glob.glob("/sys/class/devfreq/*.gpu/governor")
PERF_MODES = [("Sparen", ["powersave"], ["powersave"]),
              ("Ausgewogen", ["schedutil", "ondemand"], ["simple_ondemand"]),
              ("Leistung", ["performance"], ["performance"])]


def perf_get():
    g = rd(CPU_GOV[0]) if CPU_GOV else None
    for i, (_name, cpu, _gpu) in enumerate(PERF_MODES):
        if g in cpu:
            return i
    return 1


def perf_set(i):
    _name, cpu, gpu = PERF_MODES[i]
    for path, wanted in [(p, cpu) for p in CPU_GOV] + [(p, gpu) for p in GPU_GOV]:
        avail = (rd(path.replace("scaling_governor", "scaling_available_governors")
                    .replace("/governor", "/available_governors")) or "").split()
        gov = next((g for g in wanted if g in avail), wanted[0])
        wr(path, gov)
    log("Leistung:", PERF_MODES[i][0])


def battery():
    for d in glob.glob("/sys/class/power_supply/*"):
        if rd(d + "/type") == "Battery":
            cap = rd(d + "/capacity")
            return (int(cap) if cap and cap.isdigit() else None), rd(d + "/status") == "Charging"
    return None, False


def wifi_state():
    on = None
    out = run(["nmcli", "-t", "-f", "WIFI", "radio"])
    if out is not None:
        on = out.strip() == "enabled"
    ssid = None
    out = run(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"])
    for line in (out or "").splitlines():
        name, _, typ = line.rpartition(":")
        if "wireless" in typ:
            ssid = name.replace("\\:", ":")
    if ssid is None:
        out = run(["iwctl", "station", "wlan0", "show"])
        m = re.search(r"Connected network\s+(.+?)\s*$", re.sub(r"\x1b\[[0-9;]*m", "", out or ""), re.M)
        if m:
            ssid = m.group(1)
    if on is None:
        on = ssid is not None or rd("/sys/class/net/wlan0/operstate") == "up"
    return on, ssid


def wifi_set(on):
    if shutil.which("wifictl"):
        return spawn(["wifictl", "enable" if on else "disable"])
    return spawn(["nmcli", "radio", "wifi", "on" if on else "off"])


_bt_last = [None]


def bt_state():
    out = run(["bluetoothctl", "show"], timeout=4)
    line = next((l.strip() for l in (out or "").splitlines() if "Powered" in l), None)
    if line != _bt_last[0]:   # Diagnose: nur bei Änderung melden
        log("Bluetooth-Status:", line or ("keine Antwort" if out is None else "kein Adapter"))
        _bt_last[0] = line
    if not out:
        return False, 0
    devs = run(["bluetoothctl", "devices", "Connected"], timeout=4) or ""
    return "Powered: yes" in out, sum(1 for l in devs.splitlines() if l.startswith("Device "))


def bt_set(on):
    log("Bluetooth", "einschalten" if on else "ausschalten")
    return spawn(["bluetoothctl", "power", "on" if on else "off"])


EMULATORS = {"retroarch": "RetroArch", "drastic": "DraStic", "dsperate": "DSperate",
             "ppsspp": "PPSSPP", "mupen64plus": "Mupen64Plus", "flycast": "Flycast",
             "duckstation": "DuckStation", "melonds": "melonDS", "mgba": "mGBA"}
SYSTEMS = {"nds": "Nintendo DS", "gba": "Game Boy Advance", "gb": "Game Boy",
           "gbc": "Game Boy Color", "snes": "Super Nintendo", "nes": "NES",
           "psx": "PlayStation", "n64": "Nintendo 64", "megadrive": "Mega Drive",
           "genesis": "Genesis", "mastersystem": "Master System", "psp": "PSP",
           "dreamcast": "Dreamcast", "arcade": "Arcade"}


def running_game():
    """Sucht einen laufenden Emulator und leitet Spiel/System aus der Befehlszeile ab."""
    try:
        uptime = float(rd("/proc/uptime").split()[0])
        hz = os.sysconf("SC_CLK_TCK")
    except (AttributeError, ValueError, OSError):
        uptime, hz = None, 100
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        comm = (rd(f"/proc/{pid}/comm") or "").lower()
        emu = next((v for k, v in EMULATORS.items() if comm.startswith(k)), None)
        if not emu:
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                args = [a.decode("utf-8", "replace") for a in f.read().split(b"\0") if a]
        except OSError:
            args = []
        rom = next((a for a in reversed(args) if "/roms/" in a), args[-1] if len(args) > 1 else "")
        name = re.sub(r"\s*[\(\[].*?[\)\]]", "", os.path.splitext(os.path.basename(rom))[0]).strip()
        m = re.search(r"/roms/([^/]+)/", rom)
        system = SYSTEMS.get(m.group(1), m.group(1)) if m else ""
        played = None
        try:
            start = int(rd(f"/proc/{pid}/stat").rsplit(")", 1)[1].split()[19]) / hz
            played = uptime - start if uptime else None
        except (AttributeError, IndexError, ValueError):
            pass
        return {"pid": int(pid), "emu": emu, "name": name or emu, "system": system,
                "played": played}
    return None


# --------------------------------------------------------- Darstellung -------

THEMES = {
    "dark": {"bg": "373737", "card": "262626", "tile": "4a4a4a", "seg": "444444",
             "track": "5a5a5a", "focus": "5a5a5a", "text": "ffffff", "muted": "bdbdbd",
             "on_bg": "ffffff", "on_text": "1c1c1c", "pill": "262626", "dot": "6a6a6a"},
    "light": {"bg": "e9e9e9", "card": "ffffff", "tile": "dcdcdc", "seg": "e4e4e4",
              "track": "cfcfcf", "focus": "dedede", "text": "1c1c1c", "muted": "666666",
              "on_bg": "1c1c1c", "on_text": "ffffff", "pill": "ffffff", "dot": "b5b5b5"},
}
WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]
PAGES = ["Schnelleinstellungen", "Spiel", "RetroAchievements"]
TILES = ["WLAN", "Bluetooth", "Unterer Screen aus", "Ruhemodus"]


class ControlCenter:
    """Zustand, Zeichnen und Bedienung des Kontrollcenters."""

    def __init__(self):
        self.cfg = load_config()
        self.T = THEMES.get(self.cfg.get("theme"), THEMES["dark"])
        self.accent = (self.cfg.get("accent") or "#e5383b").lstrip("#")
        self.backlights = find_backlights(self.cfg)
        log("Regler:", ", ".join(f"{label} = {b.name}" for label, b in self.backlights) or "keine Helligkeit gefunden")
        self.page = 0
        self.focus = 0          # Zeile auf Seite 1
        self.tile = 0           # Spalte in der Kachelzeile
        self.values = {}
        self.perf = 1
        self.perf_sel = 1       # Auswahl mit links/rechts, übernommen mit A
        self.wifi = (None, None)
        self.bt = (False, 0)
        self.bat = (None, False)
        self.game = None
        self.hits = []          # (x, y, w, h, aktion) in Entwurfs-Koordinaten
        self.tracks = {}        # Regler -> (x0, x1)
        self.touch = None
        self.drag = None
        self.vol_sent = 0.0
        self.status_at = 0.0
        self.pen = None

    # -- Daten --
    def rows(self):
        r = [("slider", i) for i in range(len(self.backlights))] + [("slider", "vol")]
        return r + [("perf", None), ("tiles", None)]

    def refresh(self, full=False):
        if full:
            for i, (_label, b) in enumerate(self.backlights):
                self.values[i] = b.get()
            v = volume_get()
            self.values["vol"] = v if v is not None else self.values.get("vol", 50)
            self.perf = self.perf_sel = perf_get()
            self.game = running_game()
        self.bat = battery()
        self.wifi = wifi_state()
        self.bt = bt_state()
        self.status_at = time.monotonic()

    # -- Werte ändern --
    def set_slider(self, key, pct, final=False):
        pct = max(0, min(100, round(pct)))
        self.values[key] = pct
        if key == "vol":
            now = time.monotonic()
            if final or now - self.vol_sent > 0.08:
                volume_set(pct)
                self.vol_sent = now
        else:
            self.backlights[key][1].set(pct)

    def set_perf(self, i):
        i = max(0, min(len(PERF_MODES) - 1, i))
        if i != self.perf:
            self.perf = i
            perf_set(i)

    def press_tile(self, i):
        if i == 0:
            on = not self.wifi[0]
            if wifi_set(on):
                self.wifi = (on, self.wifi[1] if on else None)
                self.status_at = time.monotonic() - 2  # bald neu abfragen
        elif i == 1:
            on = not self.bt[0]
            if bt_set(on):
                self.bt = (on, self.bt[1] if on else 0)
                self.status_at = time.monotonic() - 2
        else:
            log(TILES[i] + ": kommt in einem der nächsten Schritte")

    # -- Bedienung mit Tasten --
    def nav(self, dx, dy):
        if self.page != 0:
            return
        rows = self.rows()
        if dy:
            self.focus = max(0, min(len(rows) - 1, self.focus + dy))
            return
        kind, key = rows[self.focus]
        if kind == "slider":
            self.set_slider(key, self.values.get(key, 50) + 5 * dx, final=True)
        elif kind == "perf":
            self.perf_sel = max(0, min(len(PERF_MODES) - 1, self.perf_sel + dx))
        elif kind == "tiles":
            self.tile = max(0, min(len(TILES) - 1, self.tile + dx))

    def confirm(self):
        if self.page != 0:
            return
        kind = self.rows()[self.focus][0]
        if kind == "tiles":
            self.press_tile(self.tile)
        elif kind == "perf":
            self.set_perf(self.perf_sel)

    def turn_page(self, d):
        self.page = max(0, min(len(PAGES) - 1, self.page + d))

    # -- Bedienung mit Touch (Pixel des Bildschirms) --
    def touch_down(self, px, py):
        if not self.pen:
            return
        x, y = self.pen.to_design(px, py)
        self.touch = (x, y, x, y)
        hit = self._hit(x, y)
        if hit and hit[0] == "slider":
            self.drag = hit[1]
            self.focus = self.rows().index(("slider", hit[1]))
            self._drag_to(x)

    def touch_move(self, px, py):
        if not (self.pen and self.touch):
            return
        x, y = self.pen.to_design(px, py)
        self.touch = self.touch[:2] + (x, y)
        if self.drag is not None:
            self._drag_to(x)

    def touch_up(self):
        if not self.touch:
            return
        x0, y0, x1, y1 = self.touch
        self.touch = None
        if self.drag is not None:
            self._drag_to(x1, final=True)
            self.drag = None
            return
        dx, dy = x1 - x0, y1 - y0
        if abs(dx) > 180 and abs(dx) > abs(dy):
            self.turn_page(-1 if dx > 0 else 1)
            return
        if abs(dx) < 30 and abs(dy) < 30:
            hit = self._hit(x0, y0)
            if not hit:
                return
            kind, val = hit
            if kind == "perf":
                self.focus = self.rows().index(("perf", None))
                self.perf_sel = val
                self.set_perf(val)
            elif kind == "tile":
                self.focus, self.tile = self.rows().index(("tiles", None)), val
                self.press_tile(val)
            elif kind == "page":
                self.page = val

    def _hit(self, x, y):
        for hx, hy, hw, hh, action in self.hits:
            if hx <= x <= hx + hw and hy <= y <= hy + hh:
                return action
        return None

    def _drag_to(self, x, final=False):
        x0, x1 = self.tracks.get(self.drag, (0, 1))
        self.set_slider(self.drag, (x - x0) * 100 / (x1 - x0), final=final)

    # -- Zeichnen --
    def draw(self, cr, w, h, view):
        P = self.pen = Pen(cr, w, h)
        T = self.T
        P.fill_all(T["bg"])
        self.hits, self.tracks = [], {}
        if view == "switcher":
            self._draw_switcher(P)
            return
        if self.page == 0:
            self._draw_quick(P)
        else:
            self._draw_placeholder(P)
        # Fußzeile mit Seitenpunkten
        P.text("L1 / R1 Seite wechseln", 17, 45, 835, T["muted"])
        P.text("B Schließen", 17, 1215, 835, T["muted"], align="r")
        x = 630 - (34 + 24 * (len(PAGES) - 1)) / 2
        for i in range(len(PAGES)):
            wdt = 34 if i == self.page else 12
            P.rrect(x, 823, wdt, 12, 6, T["on_bg"] if i == self.page else T["dot"])
            self.hits.append((x - 10, 805, wdt + 20, 48, ("page", i)))
            x += wdt + 12

    def _focus_ring(self, P, x, y, w, h, r):
        P.rrect(x - 5, y - 5, w + 10, h + 10, r + 5, self.accent, stroke=4)

    def _draw_quick(self, P):
        T, A = self.T, self.accent
        now = time.localtime()
        P.text(time.strftime("%H:%M", now), 52, 45, 90, T["text"], bold=True)
        P.text(f"{WEEKDAYS[now.tm_wday]}, {now.tm_mday}. {MONTHS[now.tm_mon - 1]}", 19, 45, 118, T["muted"])

        # Status-Pillen rechts oben
        on, ssid = self.wifi
        bt_on, bt_n = self.bt
        cap, charging = self.bat
        pills = [("WLAN: " + (ssid or ("an" if on else "aus"))),
                 ("Bluetooth: " + ((f"{bt_n} Gerät" + ("e" if bt_n != 1 else "")) if bt_on and bt_n else ("an" if bt_on else "aus"))),
                 ((f"Akku {cap} %" if cap is not None else "Akku ?") + (" · lädt" if charging else ""))]
        x = 1215
        for label in reversed(pills):
            wdt = P.width(label, 19, bold=True) + 48
            x -= wdt
            P.rrect(x, 70, wdt, 54, 27, T["pill"])
            P.text(label, 19, x + 24, 104, T["text"], bold=True)
            x -= 14

        # Läuft gerade
        P.rrect(45, 145, 1170, 135, 24, T["card"])
        P.rrect(72, 167, 90, 90, 14, T["tile"])
        P.text((self.game["name"][:1] if self.game else "–").upper(), 40, 117, 227, T["muted"], bold=True, align="c")
        P.text("LÄUFT GERADE", 15, 187, 182, T["muted"], bold=True)
        if self.game:
            g = self.game
            P.text(g["name"][:34], 28, 187, 222, T["text"], bold=True)
            sub = " · ".join(p for p in (g["system"], g["emu"]) if p)
            if g["played"] is not None:
                mins = int(g["played"] // 60)
                sub += f" · {mins // 60}:{mins % 60:02d} h"
            P.text(sub, 18, 187, 253, T["muted"])
            P.rrect(955, 181, 233, 63, 32, A, a=0.45)
            P.text("Spiel beenden", 21, 1071, 220, "ffffff", bold=True, align="c")
        else:
            P.text("Kein Spiel aktiv", 28, 187, 222, T["text"], bold=True)
            P.text("EmulationStation", 18, 187, 253, T["muted"])

        # Regler
        rows = self.rows()
        sliders = [r for r in rows if r[0] == "slider"]
        y = 300
        card_h = 98 + (len(sliders) - 1) * 76
        P.rrect(45, y, 1170, card_h, 24, T["card"])
        for n, (_kind, key) in enumerate(sliders):
            cy = y + 49 + n * 76
            if rows[self.focus] == ("slider", key):
                P.rrect(57, cy - 36, 1146, 72, 14, T["focus"])
            label = "Lautstärke" if key == "vol" else self.backlights[key][0]
            P.text(label, 22, 80, cy + 8, T["text"], bold=True)
            val = self.values.get(key, 0)
            x0, x1 = 313, 1111
            P.rrect(x0, cy - 6, x1 - x0, 12, 6, T["track"])
            P.rrect(x0, cy - 6, max(12, (x1 - x0) * val / 100), 12, 6, T["on_bg"])
            P.circle(x0 + (x1 - x0) * val / 100, cy, 11, A)
            P.text(f"{val} %", 20, 1183, cy + 7, T["text"], bold=True, align="r")
            self.tracks[key] = (x0, x1)
            self.hits.append((57, cy - 38, 1146, 76, ("slider", key)))
        y += card_h + 20

        # Leistung
        P.rrect(45, y, 1170, 90, 24, T["card"])
        P.text("Leistung", 22, 80, y + 53, T["text"], bold=True)
        focused = rows[self.focus][0] == "perf"
        for i, (name, _c, _g) in enumerate(PERF_MODES):
            sx = 372 + i * 279
            active = i == self.perf
            P.rrect(sx, y + 14, 269, 61, 16, T["on_bg"] if active else T["seg"])
            P.text(name, 20, sx + 134, y + 52, T["on_text"] if active else T["text"],
                   bold=active, align="c")
            if focused and i == self.perf_sel:
                self._focus_ring(P, sx, y + 14, 269, 61, 16)
            self.hits.append((sx, y + 10, 269, 70, ("perf", i)))
        y += 110

        # Kacheln
        states = [bool(self.wifi[0]), bool(self.bt[0]), False, False]
        focused = rows[self.focus][0] == "tiles"
        for i, name in enumerate(TILES):
            tx = 45 + i * 297
            soon = i >= 2
            P.rrect(tx, y, 282, 118, 24, T["on_bg"] if states[i] else T["tile"], a=0.5 if soon else 1)
            P.text(name, 21, tx + 25, y + 79, T["on_text"] if states[i] else T["text"], bold=True)
            if soon:
                P.text("bald", 15, tx + 25, y + 42, T["muted"])
            if focused and i == self.tile:
                self._focus_ring(P, tx, y, 282, 118, 24)
            self.hits.append((tx, y, 282, 118, ("tile", i)))

    def _draw_placeholder(self, P):
        T = self.T
        P.text(PAGES[self.page], 44, 630, 420, T["text"], bold=True, align="c")
        stage = "Etappe 2" if self.page == 1 else "Etappe 3"
        P.text(f"kommt in {stage}", 22, 630, 470, T["muted"], align="c")

    def _draw_switcher(self, P):
        T = self.T
        P.text("Gameswitcher", 44, 630, 420, T["text"], bold=True, align="c")
        P.text("kommt in Etappe 5", 22, 630, 470, T["muted"], align="c")
        P.text("Home oder B: schließen", 17, 630, 835, T["muted"], align="c")


# ------------------------------------------------------------ Overlay-App ----

class Overlay:
    def __init__(self, painter, toucher):
        self.painter = painter          # painter(cr, w, h, view)
        self.toucher = toucher          # toucher(art, x, y)
        self.display = wl.wl_display_connect(None)
        if not self.display:
            sys.exit("Keine Verbindung zu Wayland (XDG_RUNTIME_DIR/WAYLAND_DISPLAY prüfen)")
        self.compositor = self.shm = self.layer_shell = self.seat = self.touch = None
        self.outputs = {}  # proxy -> name
        self.surface = self.lsurf = self.buffer = None
        self.view = None
        self.size = None
        self.touch_id = None
        self._mm = None

        self.registry = marshal(self.display, 1, IF_REGISTRY, ("n", None))
        G = CFUNCTYPE(None, c_void_p, c_void_p, c_uint32, c_char_p, c_uint32)
        R = CFUNCTYPE(None, c_void_p, c_void_p, c_uint32)
        listen(self.registry, G(self._on_global), R(lambda *a: None))
        wl.wl_display_roundtrip(self.display)
        wl.wl_display_roundtrip(self.display)
        if not (self.compositor and self.shm and self.layer_shell):
            sys.exit("Compositor bietet keine Layer-Shell an")
        self.output = next((o for o, n in self.outputs.items() if n == OUTPUT_NAME), None)
        log("Bildschirme:", ", ".join(self.outputs.values()) or "?",
            "| verwende", OUTPUT_NAME if self.output else "Standard")
        log("Touch:", "ja" if self.touch else "nicht gefunden")

    def _bind(self, name, iface, version):
        return marshal(self.registry, 0, iface, ("u", name), ("s", iface.name),
                       ("u", version), ("n", None), version=version)

    @safe
    def _on_global(self, _data, _reg, name, iface, version):
        if iface == b"wl_compositor":
            self.compositor = self._bind(name, IF_COMPOSITOR, min(version, 4))
        elif iface == b"wl_shm":
            self.shm = self._bind(name, IF_SHM, 1)
        elif iface == b"zwlr_layer_shell_v1":
            self.layer_shell = self._bind(name, IF_LAYER_SHELL, min(version, 4))
        elif iface == b"wl_output":
            out = self._bind(name, IF_OUTPUT, min(version, 4))
            self.outputs[out] = "?"
            self._listen_output(out)
        elif iface == b"wl_seat" and not self.seat:
            self.seat = self._bind(name, IF_SEAT, min(version, 5))
            listen(self.seat,
                   CFUNCTYPE(None, c_void_p, c_void_p, c_uint32)(self._on_caps),
                   CFUNCTYPE(None, c_void_p, c_void_p, c_char_p)(lambda *a: None))

    def _listen_output(self, out):
        def on_name(_d, proxy, nm):
            self.outputs[proxy] = nm.decode()
        noop = lambda *a: None
        listen(out,
               CFUNCTYPE(None, c_void_p, c_void_p, c_int32, c_int32, c_int32, c_int32,
                         c_int32, c_char_p, c_char_p, c_int32)(noop),
               CFUNCTYPE(None, c_void_p, c_void_p, c_uint32, c_int32, c_int32, c_int32)(noop),
               CFUNCTYPE(None, c_void_p, c_void_p)(noop),
               CFUNCTYPE(None, c_void_p, c_void_p, c_int32)(noop),
               CFUNCTYPE(None, c_void_p, c_void_p, c_char_p)(on_name),
               CFUNCTYPE(None, c_void_p, c_void_p, c_char_p)(noop))

    # -- Touch (wl_touch Version 5: down, up, motion, frame, cancel) --
    @safe
    def _on_caps(self, _d, seat, caps):
        log("Eingabe-Fähigkeiten des Compositors:",
            ", ".join(n for b, n in ((1, "Maus"), (2, "Tastatur"), (4, "Touch")) if caps & b) or "keine")
        if caps & SEAT_CAP_TOUCH and not self.touch:
            self.touch = marshal(seat, 2, IF_TOUCH, ("n", None))   # get_touch
            noop = lambda *a: None
            listen(self.touch,
                   CFUNCTYPE(None, c_void_p, c_void_p, c_uint32, c_uint32, c_void_p,
                             c_int32, c_int32, c_int32)(self._t_down),
                   CFUNCTYPE(None, c_void_p, c_void_p, c_uint32, c_uint32, c_int32)(self._t_up),
                   CFUNCTYPE(None, c_void_p, c_void_p, c_uint32, c_int32, c_int32, c_int32)(self._t_motion),
                   CFUNCTYPE(None, c_void_p, c_void_p)(noop),
                   CFUNCTYPE(None, c_void_p, c_void_p)(self._t_cancel))

    @safe
    def _t_down(self, _d, _t, _serial, _time, surface, tid, x, y):
        if self.touch_id is None and self.view:
            self.touch_id = tid
            self.toucher("down", x / 256, y / 256)

    @safe
    def _t_motion(self, _d, _t, _time, tid, x, y):
        if tid == self.touch_id:
            self.toucher("move", x / 256, y / 256)

    @safe
    def _t_up(self, _d, _t, _serial, _time, tid):
        if tid == self.touch_id:
            self.touch_id = None
            self.toucher("up", 0, 0)

    @safe
    def _t_cancel(self, _d, _t):
        if self.touch_id is not None:
            self.touch_id = None
            self.toucher("up", 0, 0)

    # -- anzeigen / verbergen --
    def show(self, view):
        if self.surface:
            self.hide(quiet=True)
        self.view = view
        self.surface = marshal(self.compositor, 0, IF_SURFACE, ("n", None))
        self.lsurf = marshal(self.layer_shell, 0, IF_LAYER_SURFACE, ("n", None),
                             ("o", self.surface), ("o", self.output),
                             ("u", LAYER_OVERLAY), ("s", b"rds-controlcenter"))
        listen(self.lsurf,
               CFUNCTYPE(None, c_void_p, c_void_p, c_uint32, c_uint32, c_uint32)(self._on_configure),
               CFUNCTYPE(None, c_void_p, c_void_p)(lambda *a: self.hide()))
        marshal(self.lsurf, 1, None, ("u", ANCHOR_ALL))     # set_anchor
        marshal(self.lsurf, 2, None, ("i", -1))             # set_exclusive_zone
        marshal(self.surface, 6, None)                      # commit
        wl.wl_display_flush(self.display)
        log("angezeigt:", view)

    @safe
    def _on_configure(self, _d, lsurf, serial, w, h):
        marshal(lsurf, 6, None, ("u", serial))          # ack_configure
        self.size = (w or 1024, h or 768)
        self.redraw()

    def redraw(self):
        if not (self.surface and self.size):
            return
        try:
            self._render(*self.size)
        except Exception as exc:
            log("Fehler beim Zeichnen:", exc)

    def _render(self, w, h):
        stride = w * 4
        size = stride * h
        fd = os.memfd_create("rds-cc", 0)
        os.ftruncate(fd, size)
        mm = mmap.mmap(fd, size)
        ptr = ctypes.addressof(c_char.from_buffer(mm))
        surf = cairo.cairo_image_surface_create_for_data(ptr, 0, w, h, stride)
        cr = cairo.cairo_create(surf)
        try:
            self.painter(cr, w, h, self.view)
        finally:
            cairo.cairo_surface_flush(surf)
            cairo.cairo_destroy(cr)
            cairo.cairo_surface_destroy(surf)
        pool = marshal(self.shm, 0, IF_SHM_POOL, ("n", None), ("h", fd), ("i", size))
        old = self.buffer
        self.buffer = marshal(pool, 0, IF_BUFFER, ("n", None), ("i", 0), ("i", w),
                              ("i", h), ("i", stride), ("u", 0))  # ARGB8888
        marshal(pool, 1, None, destroy=True)                    # pool.destroy
        os.close(fd)
        marshal(self.surface, 1, None, ("o", self.buffer), ("i", 0), ("i", 0))  # attach
        marshal(self.surface, 9, None, ("i", 0), ("i", 0), ("i", w), ("i", h))  # damage_buffer
        marshal(self.surface, 6, None)                                          # commit
        if old:
            marshal(old, 0, None, destroy=True)
        self._mm = mm
        wl.wl_display_flush(self.display)

    def hide(self, quiet=False):
        if self.lsurf:
            marshal(self.lsurf, 7, None, destroy=True)
        if self.surface:
            marshal(self.surface, 0, None, destroy=True)
        if self.buffer:
            marshal(self.buffer, 0, None, destroy=True)
        self.lsurf = self.surface = self.buffer = None
        self.view = self.size = self.touch_id = None
        wl.wl_display_flush(self.display)
        if not quiet:
            log("verborgen")

    # -- Ereignisschleife --
    def pump(self, timeout, extra_fds):
        d = self.display
        while wl.wl_display_prepare_read(d) != 0:
            wl.wl_display_dispatch_pending(d)
        wl.wl_display_flush(d)
        wfd = wl.wl_display_get_fd(d)
        ready, _, _ = select.select([wfd] + extra_fds, [], [], timeout)
        if wfd in ready:
            wl.wl_display_read_events(d)
        else:
            wl.wl_display_cancel_read(d)
        wl.wl_display_dispatch_pending(d)
        return [fd for fd in ready if fd != wfd]


# ----------------------------------------------------------------- Tasten ----

EV_KEY, EV_ABS = 1, 3
ABS_HAT0X, ABS_HAT0Y = 16, 17
BTN_SOUTH, BTN_EAST, BTN_TL, BTN_TR, BTN_MODE, BTN_Z = 304, 305, 310, 311, 316, 309
DPAD = {544: (0, -1), 545: (0, 1), 546: (-1, 0), 547: (1, 0)}   # BTN_DPAD_*
KNOWN_UNUSED = {307, 308, 312, 313, 314, 315}   # X, Y, L2, R2, Select, Start
EVIOCGRAB = 0x40044590
EVENT = struct.Struct("llHHi")


def find_event(name):
    block_name = None
    with open("/proc/bus/input/devices") as f:
        for line in f:
            if line.startswith("N: Name="):
                block_name = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("H: Handlers=") and block_name == name:
                for part in line.split("=", 1)[1].split():
                    if part.startswith("event"):
                        return "/dev/input/" + part
    return None


def open_event(name):
    path = find_event(name)
    if not path:
        log("Eingabegerät nicht gefunden:", name)
        return None
    log("Eingabegerät", name, "->", path)
    return os.open(path, os.O_RDONLY | os.O_NONBLOCK)


def read_events(fd):
    try:
        data = os.read(fd, EVENT.size * 64)
    except BlockingIOError:
        return []
    out = []
    for off in range(0, len(data) - EVENT.size + 1, EVENT.size):
        _s, _us, typ, code, value = EVENT.unpack_from(data, off)
        if typ in (EV_KEY, EV_ABS):
            out.append((typ, code, value))
    return out


def grab(fd, on):
    try:
        fcntl.ioctl(fd, EVIOCGRAB, 1 if on else 0)
    except OSError as exc:
        log("Grab", "an" if on else "aus", "fehlgeschlagen:", exc)


# ------------------------------------------------------------------- main ----

def main():
    log("RetroDualStation Kontrollcenter", VERSION)
    cc = ControlCenter()
    state = {"dirty": False}

    def on_touch(kind, x, y):
        if ui.view != "cc":
            return
        {"down": cc.touch_down, "move": cc.touch_move}.get(kind, lambda *_: cc.touch_up())(x, y)
        state["dirty"] = True

    ui = Overlay(cc.draw, on_touch)
    joy = open_event(JOYPAD_NAME)
    home = open_event(HOME_NAME)
    fds = [fd for fd in (joy, home) if fd is not None]
    mode_down = combo = False
    grabbed = False

    def set_grab(on):
        nonlocal grabbed
        if joy is not None and grabbed != on:
            grab(joy, on)
            grabbed = on

    def toggle(view):
        if ui.view == view:
            ui.hide()
            set_grab(False)
        else:
            if view == "cc":
                cc.refresh(full=True)
            ui.show(view)          # wechselt auch direkt zwischen den Ansichten
            set_grab(True)

    def handle_joy(typ, code, value):
        nonlocal mode_down, combo
        if typ == EV_KEY and code == BTN_MODE:
            if value == 1:
                mode_down, combo = True, False
            elif value == 0:
                if mode_down and not combo:
                    toggle("cc")
                mode_down = False
            return
        pressed = value != 0 if typ == EV_ABS else value == 1
        if not pressed:
            return
        if mode_down:
            combo = True  # Teil einer Tastenkombination
            return
        if not ui.view:
            return
        if typ == EV_ABS and code in (ABS_HAT0X, ABS_HAT0Y):
            d = 1 if value > 0 else -1
            cc.nav(d, 0) if code == ABS_HAT0X else cc.nav(0, d)
        elif typ == EV_KEY and code in DPAD:
            cc.nav(*DPAD[code])
        elif typ == EV_KEY and code == BTN_SOUTH:
            toggle(ui.view)
            return
        elif typ == EV_KEY and code == BTN_EAST:
            cc.confirm()
        elif typ == EV_KEY and code in (BTN_TL, BTN_TR):
            cc.turn_page(-1 if code == BTN_TL else 1)
        elif typ == EV_KEY and code not in KNOWN_UNUSED:
            log("Taste ohne Funktion:", code)
            return
        else:
            return
        state["dirty"] = True

    log("bereit – Anbernic-Taste: Kontrollcenter, Home-Taste: Gameswitcher, Strg+C: Ende")
    last_minute = time.strftime("%H:%M")
    try:
        while True:
            for fd in ui.pump(1.0, fds):
                for typ, code, value in read_events(fd):
                    if fd == home:
                        if typ == EV_KEY and code == BTN_Z and value == 1:
                            toggle("switcher")
                    else:
                        handle_joy(typ, code, value)
            if ui.view == "cc":
                if time.monotonic() - cc.status_at > 5:
                    cc.refresh()
                    state["dirty"] = True
                if time.strftime("%H:%M") != last_minute:
                    last_minute = time.strftime("%H:%M")
                    state["dirty"] = True
            if state["dirty"]:
                state["dirty"] = False
                ui.redraw()
    except KeyboardInterrupt:
        pass
    finally:
        set_grab(False)
        if ui.view:
            ui.hide()
        log("beendet")


if __name__ == "__main__":
    main()
