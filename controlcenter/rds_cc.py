#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""RetroDualStation Kontrollcenter – Prototyp 0.9

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
   "backlight_top": "<name>", "backlight_bottom": "<name>",
   "keyboard": "qwertz" | "qwerty"   (sonst nach Systemsprache),
   "touch_swap": true|false, "touch_flip_x": true|false, "touch_flip_y": true|false}
"""
import ctypes
import fcntl
import glob
import json
import math
import mmap
import os
import re
import select
import shutil
import signal
import socket
import struct
import threading
import subprocess
import sys
import time
import traceback
from ctypes import (CDLL, CFUNCTYPE, POINTER, Structure, Union, byref, c_char,
                    c_char_p, c_double, c_int, c_int32, c_uint32, c_void_p, cast,
                    pointer)

VERSION = "0.12.0"
OUTPUT_NAME = os.environ.get("RDS_CC_OUTPUT", "DSI-1")
TOP_OUTPUT = os.environ.get("RDS_CC_TOP_OUTPUT", "DSI-2")
JOYPAD_NAME = os.environ.get("RDS_CC_JOYPAD", "retrogame_joypad")
HOME_NAME = os.environ.get("RDS_CC_HOMEKEY", "adc-keys-back")
TOUCH_NAME = os.environ.get("RDS_CC_TOUCH", "Goodix Capacitive TouchScreen")
POWER_NAME = "rk805 pwrkey"
POWER_LONG_MS = 800   # ab hier gilt es als langer Druck → suspend
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
            "wl_display_prepare_read", "wl_display_read_events", "wl_display_get_fd",
            "wl_display_get_error"):
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


# ------------------------------------------------------------- Sprachen ------
# Deutsch ist die Grundsprache im Code; Englisch für alle anderen Systemsprachen.

LANG = ["de"]

EN = {
    "Aktualisieren": "Refresh", "Suchen": "Search", "Sucht …": "Searching …", "Zurück": "Back",
    "An": "On", "Aus": "Off", "Verbinden": "Connect", "Trennen": "Disconnect",
    "Vergessen": "Forget", "Passwort …": "Password …", "Koppeln": "Pair", "Entfernen": "Remove",
    "A Auswählen": "A Select", "B Zurück": "B Back", "WLAN": "Wi-Fi",
    "Gespeicherte Netze": "Saved networks", "Weitere Netze": "Other networks",
    "Gekoppelte Geräte": "Paired devices", "Gefundene Geräte": "Found devices",
    "Abbrechen": "Cancel", "Zeigen": "Show", "Verbergen": "Hide",
    "Passwort eingeben": "Enter password", "Text eingeben": "Enter text", "Leerzeichen": "Space",
    "Links/Rechts wählen · A einfügen · B schließen": "Left/Right choose · A insert · B close",
    "A Taste (halten: ä, ö, ü …) · B Löschen · L1 Groß · R1 ?123 · Stick Cursor · Start OK":
        "A key (hold for ä, é, ñ …) · B delete · L1 shift · R1 ?123 · Stick cursor · Start OK",
    "L1 / R1 Seite wechseln": "L1 / R1 switch page",
    "A Ein/Aus  ·  X / Y Details": "A on/off  ·  X / Y details",
    "B Schließen": "B Close", "Kontrollcenter": "Control Center",
    "LÄUFT GERADE": "NOW PLAYING", "Spiel beenden": "Quit game", "Kein Spiel aktiv": "No game running",
    "Helligkeit oben": "Top brightness", "Helligkeit unten": "Bottom brightness",
    "Lautstärke": "Volume", "Leistung": "Performance", "Sparen": "Battery saver",
    "Ausgewogen": "Balanced", "Unterer Screen aus": "Bottom screen off", "Ruhemodus": "Sleep",
    "Neu starten": "Restart", "Ausschalten": "Power off", "ES neu starten": "Restart ES",
    "Neu starten + Logs sichern": "Restart + save logs",
    "Weiterspielen": "Resume", "Optionen (bald)": "Options (soon)", "Schließen": "Close",
    "Noch keine Spiele gespielt": "No games played yet", "Home oder B: schließen": "Home or B: close",
    "Spielstand über das Spiel selbst": "Progress is saved by the game itself",
    "gerade eben": "just now", "Spiel wird gestartet …": "Starting game …",
    "Spiel wird gespeichert …": "Saving game …",
    "Wird fortgesetzt …": "Resuming …", "Wird neu gestartet …": "Restarting …",
    "ES wirklich neu starten?": "Really restart ES?",
    "Laufendes Spiel geht verloren.": "The running game will be lost.",
    "Ja, neu starten": "Yes, restart",
    "◄ ► Auswahl  ·  A Bestätigen  ·  B Abbrechen": "◄ ► Select  ·  A Confirm  ·  B Cancel",
    "B Abbrechen  ·  X Details": "B Cancel  ·  X Details",
    "bald": "soon", "Nicht verbunden": "Not connected", "Kein Gerät": "No device",
    "Schnelleinstellungen": "Quick settings", "Spiel": "Game", "Gameswitcher": "Game switcher",
    "Home oder B: schließen": "Home or B: close", "Suche läuft …": "Searching …",
    "Suche nach Netzen …": "Searching for networks …", "Trenne …": "Disconnecting …",
    "Verbunden": "Connected", "Gespeichert": "Saved", "Gesichert": "Secured", "Offen": "Open",
    "nicht in Reichweite": "out of range", "Gekoppelt": "Paired", "Neu": "New",
    "trennen: Controller ausschalten": "to disconnect, turn controller off",
    "Netze": "networks", "Geräte": "devices", " · lädt": " · charging",
}
EN.update({k.upper(): v.upper() for k, v in list(EN.items()) if k.upper() not in EN})
_DAYS = dict(zip(["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
                 ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]))
_MONTHS = dict(zip(["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
                    "September", "Oktober", "November", "Dezember"],
                   ["January", "February", "March", "April", "May", "June", "July", "August",
                    "September", "October", "November", "December"]))
EN_PATTERNS = [
    (r"^vor (\d+) min$", lambda m: f"{m.group(1)} min ago"),
    (r"^vor (\d+) h$", lambda m: f"{m.group(1)} h ago"),
    (r"^vor (\d+) Tagen$", lambda m: f"{m.group(1)} days ago"),
    (r"^Akku (\S+) %( · lädt)?$", lambda m: f"Battery {m[1]} %" + (" · charging" if m[2] else "")),
    (r"^(\w+), (\d+)\. (\w+)$", lambda m: f"{_DAYS.get(m[1], m[1])}, {_MONTHS.get(m[3], m[3])} {m[2]}"),
    (r"^Verbunden mit (.+)$", lambda m: f"Connected to {m[1]}"),
    (r"^(WLAN|Bluetooth) ist aus$", lambda m: f"{tr(m[1])} is off"),
    (r"^(WLAN|Bluetooth) einschalten, um (\w+) zu sehen$", lambda m: f"Turn on {tr(m[1])} to see {tr(m[2])}"),
    (r"^Keine (\w+) gefunden$", lambda m: f"No {tr(m[1])} found"),
    (r"^(\d+) (\w+)  ·  mit dem Finger scrollen$", lambda m: f"{m[1]} {tr(m[2])}  ·  scroll with your finger"),
    (r"^kommt in Etappe (\d+)$", lambda m: f"coming in stage {m[1]}"),
    (r"^Suche nach Geräten … noch (\d+) s – Controller in den Kopplungsmodus versetzen$",
     lambda m: f"Searching for devices … {m[1]} s left – put your controller in pairing mode"),
    (r"^Tippe auf „(.+)“, um neue Geräte zu finden$", lambda m: f"Tap “{tr(m[1])}” to find new devices"),
    (r"^Verbinde mit (.+) …$", lambda m: f"Connecting to {m[1]} …"),
    (r"^Kopple (.+) … \(bis zu 60 s\)$", lambda m: f"Pairing {m[1]} … (up to 60 s)"),
    (r"^Verbinde (.+) …$", lambda m: f"Connecting {m[1]} …"),
    (r"^Trenne (.+) …$", lambda m: f"Disconnecting {m[1]} …"),
    (r"^(.+) getrennt – zum dauerhaften Trennen Controller ausschalten$",
     lambda m: f"{m[1]} disconnected – turn the controller off to keep it disconnected"),
    (r"^(.+) entfernt$", lambda m: f"{m[1]} removed"),
    (r"^(.+) vergessen$", lambda m: f"{m[1]} forgotten"),
    (r"^Passwort für (.+)$", lambda m: f"Password for {m[1]}"),
]


def ui_language():
    """'de' bei deutscher Systemsprache, sonst 'en'."""
    lang = ""
    try:
        with open("/storage/.config/system/configs/system.cfg") as f:
            for line in f:
                if line.startswith("system.language="):
                    lang = line.split("=", 1)[1].strip().lower()
    except OSError:
        pass
    lang = lang or os.environ.get("LANG", "de").lower()
    return "de" if lang.startswith("de") else "en"


def tr(text):
    """Übersetzt eine Oberflächen-Zeichenkette in die aktuelle Sprache."""
    if LANG[0] == "de" or not text:
        return text
    if text in EN:
        return EN[text]
    for pat, fn in EN_PATTERNS:
        m = re.match(pat, text)
        if m:
            return fn(m)
    if " · " in text:   # z. B. „Verbunden · Signal 78 %“
        return " · ".join(EN.get(part, part) for part in text.split(" · "))
    return text


# ------------------------------------------------------------------ Cairo ----

cairo = CDLL("libcairo.so.2")
cairo.cairo_image_surface_create_for_data.restype = c_void_p
cairo.cairo_image_surface_create_for_data.argtypes = [c_void_p, c_int, c_int, c_int, c_int]
cairo.cairo_image_surface_create_from_png.restype = c_void_p
cairo.cairo_image_surface_create_from_png.argtypes = [c_char_p]
for _fn in ("cairo_image_surface_get_width", "cairo_image_surface_get_height", "cairo_surface_status"):
    getattr(cairo, _fn).restype = c_int
    getattr(cairo, _fn).argtypes = [c_void_p]
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
    "cairo_line_to": [c_void_p, c_double, c_double],
    "cairo_curve_to": [c_void_p, c_double, c_double, c_double, c_double, c_double, c_double],
    "cairo_set_line_cap": [c_void_p, c_int],
    "cairo_set_line_join": [c_void_p, c_int],
    "cairo_clip": [c_void_p], "cairo_reset_clip": [c_void_p],
    "cairo_save": [c_void_p], "cairo_restore": [c_void_p],
    "cairo_translate": [c_void_p, c_double, c_double], "cairo_scale": [c_void_p, c_double, c_double],
    "cairo_set_source_surface": [c_void_p, c_void_p, c_double, c_double],
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


def mix(a, b, t):
    """Mischt zwei Farben (hex ohne #), t=0 -> a, t=1 -> b."""
    ca, cb = [int(a[i:i + 2], 16) for i in (0, 2, 4)], [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "".join("%02x" % round(x + (y - x) * t) for x, y in zip(ca, cb))


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

    _png = {}

    def image(self, path, x, y, w, h, r=0):
        """PNG eingepasst (cover) mit abgerundeten Ecken zeichnen. False, wenn nicht ladbar."""
        surf = Pen._png.get(path)
        if surf is None:
            surf = cairo.cairo_image_surface_create_from_png(path.encode())
            if not surf or cairo.cairo_surface_status(surf) != 0:
                Pen._png[path] = False
                return False
            Pen._png[path] = surf
        if surf is False:
            return False
        iw, ih = cairo.cairo_image_surface_get_width(surf), cairo.cairo_image_surface_get_height(surf)
        if iw <= 0 or ih <= 0:
            return False
        cr, s = self.cr, self.s
        X, Y, W, H = self.X(x), self.Y(y), w * s, h * s
        R = min(r * s, W / 2, H / 2)
        cairo.cairo_save(cr)
        cairo.cairo_new_path(cr)
        cairo.cairo_new_sub_path(cr)
        cairo.cairo_arc(cr, X + W - R, Y + R, R, -PI / 2, 0)
        cairo.cairo_arc(cr, X + W - R, Y + H - R, R, 0, PI / 2)
        cairo.cairo_arc(cr, X + R, Y + H - R, R, PI / 2, PI)
        cairo.cairo_arc(cr, X + R, Y + R, R, PI, 3 * PI / 2)
        cairo.cairo_close_path(cr)
        cairo.cairo_clip(cr)
        k = max(W / iw, H / ih)
        cairo.cairo_translate(cr, X + (W - iw * k) / 2, Y + (H - ih * k) / 2)
        cairo.cairo_scale(cr, k, k)
        cairo.cairo_set_source_surface(cr, surf, 0, 0)
        cairo.cairo_paint(cr)
        cairo.cairo_restore(cr)
        return True

    def clip(self, x, y, w, h):
        cairo.cairo_new_path(self.cr)
        cairo.cairo_rectangle(self.cr, self.X(x), self.Y(y), w * self.s, h * self.s)
        cairo.cairo_clip(self.cr)

    def unclip(self):
        cairo.cairo_reset_clip(self.cr)

    def circle(self, x, y, r, c):
        cairo.cairo_new_path(self.cr)
        cairo.cairo_arc(self.cr, self.X(x), self.Y(y), r * self.s, 0, 2 * PI)
        self.color(c)
        cairo.cairo_fill(self.cr)

    def chevron(self, x, y, size, c, width=4):
        """Pfeil „›“ mit Spitze bei (x, y)."""
        cr, s = self.cr, self.s
        cairo.cairo_new_path(cr)
        h = abs(size)
        cairo.cairo_move_to(cr, self.X(x - size / 2), self.Y(y - h))
        cairo.cairo_line_to(cr, self.X(x + size / 2), self.Y(y))
        cairo.cairo_line_to(cr, self.X(x - size / 2), self.Y(y + h))
        cairo.cairo_set_line_cap(cr, 1)
        cairo.cairo_set_line_width(cr, width * s)
        self.color(c)
        cairo.cairo_stroke(cr)

    def sun(self, cx, cy, c):
        """Sonne mit Strahlen (Symbol für den Hell-Modus)."""
        import math
        self.circle(cx, cy, 8, c)
        cr = self.cr
        cairo.cairo_new_path(cr)
        for k in range(8):
            a = k * math.pi / 4
            cairo.cairo_move_to(cr, self.X(cx + 12 * math.cos(a)), self.Y(cy + 12 * math.sin(a)))
            cairo.cairo_line_to(cr, self.X(cx + 17 * math.cos(a)), self.Y(cy + 17 * math.sin(a)))
        cairo.cairo_set_line_cap(cr, 1)
        cairo.cairo_set_line_width(cr, 3 * self.s)
        self.color(c)
        cairo.cairo_stroke(cr)

    def power_icon(self, cx, cy, r, c, width=4):
        """Power-Symbol: Kreisbogen 270° + senkrechter Strich oben."""
        import math
        cr = self.cr
        cairo.cairo_new_path(cr)
        a0 = math.pi * 0.75   # 135° (unten links)
        a1 = math.pi * 2.25   # 405° = 45° (unten rechts), also 270° Bogen
        cairo.cairo_arc(cr, self.X(cx), self.Y(cy), r * self.s, a0, a1)
        cairo.cairo_set_line_cap(cr, 1)
        cairo.cairo_set_line_width(cr, width * self.s)
        self.color(c)
        cairo.cairo_stroke(cr)
        cairo.cairo_new_path(cr)
        cairo.cairo_move_to(cr, self.X(cx), self.Y(cy - r * 0.3))
        cairo.cairo_line_to(cr, self.X(cx), self.Y(cy - r * 1.1))
        cairo.cairo_set_line_cap(cr, 1)
        cairo.cairo_set_line_width(cr, width * self.s)
        self.color(c)
        cairo.cairo_stroke(cr)

    def logo(self, x, y, h, fg, knockout, red="e5383b", blue="3d7bff"):
        """RDS-Monogramm „Verwoben“ (Logo-Entwurf Variante 3), Höhe h, oben links bei (x, y)."""
        import math
        k = h / 130
        cr = self.cr

        def pt(lx, ly, dx):
            return self.X(x + (lx + 18 + dx) * k), self.Y(y + ly * k)

        def path(kind, dx):
            cairo.cairo_new_path(cr)
            if kind == "r":       # M24 115 V15 H46 A24 25 0 0 1 46 65 H24  +  M44 65 L70 115
                cairo.cairo_move_to(cr, *pt(24, 115, dx))
                cairo.cairo_line_to(cr, *pt(24, 15, dx))
                cairo.cairo_line_to(cr, *pt(46, 15, dx))
                for i in range(1, 25):
                    a = -math.pi / 2 + math.pi * i / 24
                    cairo.cairo_line_to(cr, *pt(46 + 24 * math.cos(a), 40 + 25 * math.sin(a), dx))
                cairo.cairo_line_to(cr, *pt(24, 65, dx))
                cairo.cairo_move_to(cr, *pt(44, 65, dx))
                cairo.cairo_line_to(cr, *pt(70, 115, dx))
            elif kind == "d":     # M92 115 V15 H106 A44 50 0 0 1 106 115 H92
                cairo.cairo_move_to(cr, *pt(92, 115, dx))
                cairo.cairo_line_to(cr, *pt(92, 15, dx))
                cairo.cairo_line_to(cr, *pt(106, 15, dx))
                for i in range(1, 33):
                    a = -math.pi / 2 + math.pi * i / 32
                    cairo.cairo_line_to(cr, *pt(106 + 44 * math.cos(a), 65 + 50 * math.sin(a), dx))
                cairo.cairo_line_to(cr, *pt(92, 115, dx))
            else:                 # S als zwei Bézierkurven
                cairo.cairo_move_to(cr, *pt(208, 28, dx))
                cairo.cairo_curve_to(cr, *pt(200, 14, dx), *pt(166, 12, dx), *pt(166, 38, dx))
                cairo.cairo_curve_to(cr, *pt(166, 64, dx), *pt(212, 60, dx), *pt(212, 88, dx))
                cairo.cairo_curve_to(cr, *pt(212, 118, dx), *pt(172, 120, dx), *pt(162, 102, dx))

        def stroke(color, width):
            cairo.cairo_set_line_cap(cr, 1)
            cairo.cairo_set_line_join(cr, 1)
            cairo.cairo_set_line_width(cr, width * k * self.s)
            self.color(color)
            cairo.cairo_stroke(cr)

        path("r", 0); stroke(red, 16)
        path("d", -16); stroke(knockout, 30)     # Lücke = „verwoben“
        path("d", -16); stroke(fg, 16)
        path("s", -36); stroke(knockout, 30)
        path("s", -36); stroke(blue, 16)
        return 230 * k                            # Breite

    def text(self, txt, size, x, y, c, bold=False, align="l", raw=False):
        if not raw:
            txt = tr(txt)
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

    def width(self, txt, size, bold=False, raw=False):
        if not raw:
            txt = tr(txt)
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


def save_config(cfg):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
    except OSError as exc:
        log("Einstellungen nicht gespeichert:", exc)


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

    def set(self, pct, allow_off=False):
        raw = round(max(5, min(100, pct)) * self.max / 100)
        if allow_off and pct == 0:
            raw = 0
        wr(self.dir + "/brightness", max(0 if allow_off else 1, raw))


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
    out = run(["rfkill", "list", "wifi"])
    if out and "blocked" in out:
        on = "Soft blocked: yes" not in out and "Hard blocked: yes" not in out
        if not on:
            return False, None
    out = run(["nmcli", "-t", "-f", "WIFI", "radio"]) if on is None else None
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
    """Wie ROCKNIX: Funk frei/sperren, Einstellung setzen, beim Einschalten neu verbinden."""
    log("WLAN", "einschalten" if on else "ausschalten")
    if on:
        cmd = "set_setting wifi.enabled 1; wifictl enable; sleep 1; wifictl connect"
    else:
        cmd = "wifictl disable; set_setting wifi.enabled 0"
    return spawn(["bash", "-c", ". /etc/profile; " + cmd])


def bt_state():
    # Bei ROCKNIX läuft der Bluetooth-Dienst nur, wenn Bluetooth eingeschaltet ist
    """(an?, [Namen der verbundenen Geräte])"""
    if run(["systemctl", "is-active", "bluetooth"]) is None:
        return False, []
    out = run(["bluetoothctl", "show"], timeout=4)
    if not out:
        return True, []          # Dienst läuft, Adapter meldet sich noch nicht
    devs = run(["bluetoothctl", "devices", "Connected"], timeout=4) or ""
    names = [l.split(" ", 2)[2] for l in devs.splitlines()
             if l.startswith("Device ") and len(l.split(" ", 2)) > 2]
    return "Powered: no" not in out, names


def bt_set(on):
    log("Bluetooth", "einschalten" if on else "ausschalten")
    if on:   # wie das ES-Menü: Einstellung, Dienst und Helfer über rocknix-bluetooth
        cmd = "rocknix-bluetooth enable; sleep 1; bluetoothctl power on"
    else:
        cmd = "bluetoothctl power off; rocknix-bluetooth disable"
    return spawn(["bash", "-c", ". /etc/profile; " + cmd])


EMULATORS = {"retroarch": "RetroArch", "drastic": "DraStic", "dsperate": "DSperate",
             "ppsspp": "PPSSPP", "mupen64plus": "Mupen64Plus", "flycast": "Flycast",
             "duckstation": "DuckStation", "melonds": "melonDS", "mgba": "mGBA"}
SYSTEMS = {"nds": "Nintendo DS", "gba": "Game Boy Advance", "gb": "Game Boy",
           "gbc": "Game Boy Color", "snes": "Super Nintendo", "nes": "NES",
           "psx": "PlayStation", "n64": "Nintendo 64", "megadrive": "Mega Drive",
           "genesis": "Genesis", "mastersystem": "Master System", "psp": "PSP",
           "dreamcast": "Dreamcast", "arcade": "Arcade"}


AUTO_DIM_EMUS = ("RetroArch", "PortMaster")   # unterer Screen beim Start automatisch dunkel
PORT_RE = re.compile(r"/roms/ports/([^/]+)\.sh$")


def proc_tree(pid):
    """PID samt allen Nachfahren (Kinder zuerst)."""
    kids = {}
    for p in os.listdir("/proc"):
        if p.isdigit():
            try:
                ppid = int(rd(f"/proc/{p}/stat").rsplit(")", 1)[1].split()[1])
                kids.setdefault(ppid, []).append(int(p))
            except (AttributeError, IndexError, ValueError):
                pass
    out = []
    def walk(x):
        for k in kids.get(x, []):
            walk(k)
        out.append(x)
    walk(pid)
    return out


def _cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return [a.decode("utf-8", "replace") for a in f.read().split(b"\0") if a]
    except OSError:
        return []


ARTICLE_RE = re.compile(r"^(.+?),\s*(The|A|An|Der|Die|Das|Ein|Eine|Le|La|Les|L'|El|Los|Las|Il|Lo|Gli)\b(.*)$", re.I)


def fix_article(name):
    """„Legend of Zelda, The - Link's Awakening“ → „The Legend of Zelda - Link's Awakening“."""
    m = ARTICLE_RE.match(name or "")
    return f"{m.group(2)} {m.group(1)}{m.group(3)}" if m else name


_META = {}


def game_meta(rom):
    """Name und Icon (PNG) aus der gamelist.xml des Systems; zwischengespeichert."""
    if not rom or rom in _META:
        return _META.get(rom, (None, None))
    name = icon = None
    folder = os.path.dirname(rom)
    try:
        import xml.etree.ElementTree as ET
        rel = "./" + os.path.relpath(rom, folder)
        for g in ET.parse(os.path.join(folder, "gamelist.xml")).getroot().iter("game"):
            if g.findtext("path") == rel:
                name = (g.findtext("name") or "").strip() or None
                for tag in ("cartridge", "thumbnail", "image"):
                    v = (g.findtext(tag) or "").strip()
                    if v:
                        path = os.path.normpath(os.path.join(folder, v))
                        if path.lower().endswith(".png") and os.path.exists(path):
                            icon = path
                            break
                break
    except (OSError, ValueError, Exception):
        pass
    if not icon:   # DualStation Sync legt romname-icon.png ab
        base = os.path.splitext(os.path.basename(rom))[0]
        for sub in ("images", "media/images"):
            cand = os.path.join(folder, sub, base + "-icon.png")
            if os.path.exists(cand):
                icon = cand
                break
    _META[rom] = (name, icon)
    return name, icon


def running_port():
    """PortMaster selbst (pugwash) oder ein gestarteter Port (/roms/ports/*.sh)."""
    tool = None
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        args = _cmdline(pid)
        if not args:
            continue
        if os.path.basename(args[0]) == "bash" and len(args) > 1:
            m = PORT_RE.search(args[1])
            if m and "PortMaster" not in m.group(1):
                return {"pid": int(pid), "emu": "PortMaster", "name": m.group(1),
                        "system": "Ports", "played": None, "rom": args[1]}
        if any(os.path.basename(a) == "pugwash" for a in args[:3]):
            tool = {"pid": int(pid), "emu": "PortMaster", "name": "PortMaster",
                    "system": "", "played": None}
    return tool


def running_game():
    """Sucht einen laufenden Emulator und leitet Spiel/System aus der Befehlszeile ab."""
    g = _running_emu()
    return g or running_port()


def _running_emu():
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
        if not emu or comm.endswith(".sh"):   # Startskripte nicht einfrieren
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
        meta_name, icon = game_meta(rom if "/roms/" in rom else None)
        return {"pid": int(pid), "emu": emu, "name": fix_article(meta_name or name) or emu,
                "system": system, "played": played, "icon": icon,
                "rom": rom if "/roms/" in rom else None}
    return None


# --------------------------------------------------------------- Pause -------

RA_ADDR = ("127.0.0.1", 55355)   # RetroArch-Steuerschnittstelle (Netzwerkbefehle)


def ra_command(cmd, reply=False):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(0.3)
            sock.sendto(cmd.encode(), RA_ADDR)
            return sock.recv(4096).decode("utf-8", "replace") if reply else ""
    except OSError:
        return None


def quit_game(game):
    """Laufenden Emulator beenden (RetroArch sauber per Befehl, sonst SIGTERM)."""
    if not game:
        return
    log("Spiel beenden:", game["emu"], game["pid"])
    if game["emu"] == "RetroArch" and ra_command("QUIT") is not None:
        ra_command("QUIT")   # zweimal: RetroArch fragt sonst ggf. nach
        return
    for p in proc_tree(game["pid"]):
        try:
            os.kill(p, signal.SIGCONT)
            os.kill(p, signal.SIGTERM)
        except OSError:
            pass


# ------------------------------------------------------------ Gameswitcher --

GS_DIR = "/storage/.config/retrodualstation/switcher"
GS_HISTORY = GS_DIR + "/history.json"
GS_MAX = 12
SLOT = 9   # fester RetroArch-Slot für den Gameswitcher


def inject_keys(seq):
    """Tastendrücke ins eingebaute Joypad einspeisen (sehen alle Programme wie echte Drücke).
    seq: Liste aus (code, wert) oder Pausen in Sekunden (float)."""
    dev = next(("/dev/input/" + p.split("/")[4] for p in glob.glob("/sys/class/input/event*/device/name")
                if (rd(p) or "").strip() == JOYPAD_NAME), None)
    if not dev:
        return False
    fd = os.open(dev, os.O_WRONLY)
    try:
        for item in seq:
            if isinstance(item, float):
                time.sleep(item)
                continue
            code, val = item
            os.write(fd, EVENT.pack(0, 0, EV_KEY, code, val))
            os.write(fd, EVENT.pack(0, 0, EV_SYN, 0, 0))
    finally:
        os.close(fd)
    return True


def es_launch(rom):
    """Spiel über die ES-Schnittstelle starten (ES wählt Emulator wie beim normalen Start)."""
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:1234/launch", data=rom.encode(), method="POST")
        urllib.request.urlopen(req, timeout=5).read()
        return True
    except Exception as exc:
        log("Start über ES fehlgeschlagen:", exc)
        return False


def autosave_on(rom):
    """Auto-Speichern/Laden laut ES (system.cfg): <system>.autosave hat Vorrang vor global.autosave."""
    cfg = rd("/storage/.config/system/configs/system.cfg") or ""
    system = os.path.basename(os.path.dirname(rom or ""))
    for key in (f"{system}.autosave", "global.autosave"):
        m = re.search(rf"^{re.escape(key)}=(\S+)", cfg, re.M)
        if m:
            return m.group(1) == "1"
    return False


def sway_cmd(cmd):
    """swaymsg ohne Warten (aus dem CC heraus kann ein wartender Aufruf hängen bleiben)."""
    try:
        subprocess.Popen(["swaymsg", cmd], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True,
                         env=dict(os.environ, SWAYSOCK="/run/0-runtime-dir/sway-ipc.0.sock"))
    except OSError as exc:
        log("swaymsg fehlgeschlagen:", exc)


def rom_of(pid):
    args = _cmdline(pid)
    return next((a for a in reversed(args) if "/roms/" in a), None)


class Switcher:
    """Zuletzt gespielte Spiele: speichern beim Öffnen, fortsetzen (A) oder neu starten (Y)."""

    def __init__(self):
        self.items = []
        self.sel = 0
        self.busy = None   # Text während einer Aktion
        self.ready = False # Hintergrund-Speichern fertig → Hauptschleife pausiert und übernimmt
        self.load()

    def load(self):
        try:
            with open(GS_HISTORY) as f:
                self.items = [i for i in json.load(f) if os.path.exists(i.get("rom", ""))][:GS_MAX]
        except (OSError, ValueError):
            self.items = []

    def save(self):
        os.makedirs(GS_DIR, exist_ok=True)
        tmp = GS_HISTORY + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.items, f, indent=1)
        os.replace(tmp, GS_HISTORY)

    def remember(self, game, shot=None):
        """Laufendes Spiel oben in die Liste setzen."""
        rom = game.get("rom") or rom_of(game["pid"])
        if not rom:
            return
        old = next((i for i in self.items if i["rom"] == rom), {})
        entry = {"rom": rom, "name": game["name"], "system": game.get("system", ""),
                 "emu": game["emu"], "icon": game.get("icon"), "time": time.time(),
                 "shot": shot or old.get("shot")}
        self.items = [entry] + [i for i in self.items if i["rom"] != rom]
        self.items = self.items[:GS_MAX]
        self.save()

    def capture(self, game):
        """Beim Öffnen im Spiel: Speicherstand anlegen + Screenshot. Läuft VOR Pause und Grab."""
        if not game:
            return
        rom = game.get("rom") or rom_of(game["pid"])
        if not rom:
            return
        os.makedirs(GS_DIR, exist_ok=True)
        shot = os.path.join(GS_DIR, re.sub(r"[^\w.-]+", "_", os.path.basename(rom)) + ".png")
        emu = game["emu"]
        if emu == "RetroArch":
            ra_command(f"SAVE_STATE_SLOT {SLOT}")
            png = os.path.join("/storage/roms/savestates", os.path.basename(os.path.dirname(rom)),
                               os.path.splitext(os.path.basename(rom))[0] + f".state{SLOT}.png")
            for _ in range(15):          # Vorschaubild abwarten
                time.sleep(0.1)
                if os.path.exists(png) and time.time() - os.path.getmtime(png) < 5:
                    break
            if os.path.exists(png):
                shot = png
        else:
            # Screenshot (oberer Bildschirm, kaum komprimiert = schnell) parallel zum Speichern
            t0 = time.monotonic()
            grim = subprocess.Popen(["grim", "-l", "1", "-o", "DSI-2", shot],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if emu == "DraStic":
                dss = os.path.join("/storage/roms/savestates/nds",
                                   os.path.splitext(os.path.basename(rom))[0] + "_0.dss")
                before = os.path.getmtime(dss) if os.path.exists(dss) else 0
                inject_keys([(313, 1), 0.1, (313, 0)])   # R2 = Speicherstand
                for _ in range(30):                        # nur so lange warten, bis die Datei fertig ist
                    time.sleep(0.1)
                    if os.path.exists(dss) and os.path.getmtime(dss) > before:
                        time.sleep(0.2)                    # Schreiben abschließen lassen
                        break
            try:
                grim.wait(timeout=5)
            except subprocess.TimeoutExpired:
                grim.kill()
            log("Gameswitcher: Aufnahme + Speichern in %.1f s" % (time.monotonic() - t0))
        self.remember(game, shot if os.path.exists(shot) else None)
        log("Gameswitcher: gespeichert", emu, os.path.basename(rom))

    def resume_steps(self, item, fresh):
        """Nach dem Start (im Hintergrund): Speicherstand laden bzw. Autoload unterdrücken."""
        emu = item["emu"]
        t0 = time.monotonic()
        deadline = time.time() + 30
        if emu == "RetroArch":
            seen = False
            while time.time() < deadline:
                if not seen and run(["pidof", "retroarch"]):
                    seen = True
                    log("Gameswitcher: RetroArch-Prozess nach %.1f s" % (time.monotonic() - t0))
                    # Sicherheitsnetz: falls Sway es unten geöffnet hat, nach oben holen
                    sway_cmd('[app_id="retroarch"] move to output ' + TOP_OUTPUT)
                st = ra_command("GET_STATUS", reply=True)
                if st and "PLAYING" in st:
                    log("Gameswitcher: RetroArch laeuft nach %.1f s" % (time.monotonic() - t0))
                    sway_cmd('[app_id="retroarch"] move to output ' + TOP_OUTPUT)   # Fenster existiert jetzt sicher
                    if fresh:
                        time.sleep(0.5)
                        ra_command("RESET")      # Auto-Laden übergehen (Ladebildschirm verdeckt es)
                    elif not autosave_on(item["rom"]):
                        time.sleep(1.5)          # ohne Auto-Laden: unseren Slot nachladen
                        ra_command(f"LOAD_STATE_SLOT {SLOT}")
                    # sonst hat RetroArch den Auto-Stand schon beim Start geladen (wie bei Onion)
                    log("Gameswitcher: Stand bereit nach %.1f s" % (time.monotonic() - t0))
                    break
                time.sleep(0.25)
        elif emu == "DraStic" and not fresh:
            env = dict(os.environ, SWAYSOCK="/run/0-runtime-dir/sway-ipc.0.sock")
            def window():
                try:
                    tree = subprocess.run(["swaymsg", "-t", "get_tree"], env=env, timeout=2,
                                          capture_output=True, text=True).stdout
                    return '"drastic"' in tree.lower()
                except Exception:
                    return False
            while time.time() < deadline and not window():   # sobald das Fenster da ist
                time.sleep(0.15)
            log("Gameswitcher: DraStic-Fenster nach %.1f s" % (time.monotonic() - t0))
            time.sleep(0.4)
            inject_keys([(312, 1), 0.1, (312, 0)])   # L2 = laden
            time.sleep(1.2)
            inject_keys([(312, 1), 0.1, (312, 0)])   # zur Sicherheit erneut (gleicher Stand)
            log("Gameswitcher: Stand geladen nach %.1f s" % (time.monotonic() - t0))
        else:
            # DSperate lädt selbst (autoload), Ports/andere: warten bis der Prozess läuft + kurz Luft
            while time.time() < deadline and not running_game():
                time.sleep(0.25)
            time.sleep(2.5)
            log("Gameswitcher: %s bereit nach %.1f s" % (emu, time.monotonic() - t0))

    def launch(self, item, fresh, current=None):
        """Laufendes Spiel beenden (speichert vorher), dann item starten.
        Setzt self.done, wenn das Spiel läuft und der Stand geladen ist (Ladebildschirm weg)."""
        self.done = False
        ini = "/storage/.config/dsperate/dsperate.ini"

        def work():
            before = {p: rd(p) for p in CPU_GOV + GPU_GOV}
            restore = None
            t0 = time.monotonic()
            try:
                try:
                    perf_set(2)   # kurzzeitig volle Leistung für Beenden + Starten
                except Exception:
                    pass
                if current:
                    quit_game(current)
                    for _ in range(60):
                        if not running_game():
                            break
                        time.sleep(0.15)
                    log("Gameswitcher: altes Spiel beendet nach %.1f s" % (time.monotonic() - t0))
                    # warten, bis ES wieder bereit ist (sonst wird der Start verzögert abgearbeitet)
                    for _ in range(40):
                        try:
                            import urllib.request
                            r = urllib.request.urlopen("http://127.0.0.1:1234/runningGame", timeout=1).read()
                            if b"NO GAME" in r:
                                break
                        except Exception:
                            pass
                        time.sleep(0.15)
                    log("Gameswitcher: ES bereit nach %.1f s" % (time.monotonic() - t0))
                    for _ in range(100):          # Startskript des alten Spiels muss fertig sein
                        if not run(["pgrep", "-f", "runemu.sh"]):
                            break
                        time.sleep(0.1)
                    log("Gameswitcher: runemu beendet nach %.1f s" % (time.monotonic() - t0))
                if fresh and item["emu"] == "DSperate" and os.path.exists(ini):
                    txt = rd(ini) or ""
                    if "autoload = true" in txt:
                        restore = txt
                        wr(ini, txt.replace("autoload = true", "autoload = false"))
                log("Gameswitcher:", "neu starten" if fresh else "fortsetzen", item["name"])
                if es_launch(item["rom"]):
                    for _ in range(100):
                        if run(["pgrep", "-f", "runemu.sh"]):
                            log("Gameswitcher: runemu gestartet nach %.1f s" % (time.monotonic() - t0))
                            break
                        time.sleep(0.1)
                    self.resume_steps(item, fresh)
                log("Gameswitcher: Wechsel fertig nach %.1f s" % (time.monotonic() - t0))
            except Exception:
                log("Gameswitcher: Fehler beim Wechsel:\n" + traceback.format_exc().rstrip())
            finally:
                self.done = True
                # nur zurücksetzen, wenn ROCKNIX beim Start nichts Eigenes gesetzt hat
                for path, old in before.items():
                    if old and rd(path) == "performance" and old != "performance":
                        wr(path, old)
                if restore:
                    time.sleep(10)
                    wr(ini, restore)
        threading.Thread(target=work, daemon=True).start()


class Pauser:
    """Hält das laufende Spiel an, solange das Overlay offen ist."""

    def __init__(self):
        self.how = None
        self.pid = None

    def pause(self, game):
        if self.how or not game:
            return
        if game["emu"] == "RetroArch":
            status = ra_command("GET_STATUS", reply=True)
            if status is not None:
                if "PLAYING" in status:
                    ra_command("PAUSE_TOGGLE")
                    self.how = "ra"
                    log("Pause: RetroArch angehalten")
                else:
                    log("Pause: RetroArch meldet", status.strip()[:40], "– nichts zu tun")
                return
        try:
            self.pids = proc_tree(game["pid"])
            for p in reversed(self.pids):
                try:
                    os.kill(p, signal.SIGSTOP)
                except OSError:
                    pass
            self.how, self.pid = "stop", game["pid"]
            log("Pause:", game["emu"], "eingefroren (PID %d)" % game["pid"])
        except OSError as exc:
            log("Pause fehlgeschlagen:", exc)

    def resume(self):
        if self.how == "ra":
            ra_command("PAUSE_TOGGLE")
        elif self.how == "stop":
            for p in getattr(self, "pids", [self.pid]):
                try:
                    os.kill(p, signal.SIGCONT)
                except OSError:
                    pass
        if self.how:
            log("Pause beendet")
        self.how = self.pid = None


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
ACCENTS = ["e5383b", "3d7bff", "2bb673", "f08c00", "9b5de5", "e64980"]
PAGES = ["Schnelleinstellungen", "Spiel", "RetroAchievements"]
TILES = ["WLAN", "Bluetooth", "Unterer Screen aus", "Ruhemodus"]


def nmcli_split(line):
    return [f.replace("\\:", ":") for f in re.split(r"(?<!\\):", line)]


class SubMenu:
    """Gemeinsame Grundlage für WLAN- und Bluetooth-Untermenü."""
    title = ""
    VISIBLE = 6
    ROW = 98
    LIST_Y, LIST_H = 205, 6 * 98

    def __init__(self, cc):
        self.cc = cc
        self.items = []
        self.msg = ""
        self.loaded = False
        self.focus = 0      # 0 = Kopfzeile, 1.. = Einträge
        self.col = 0        # Spalte (Kopfzeile: Zurück/Schalter/Suchen, Eintrag: Aktion)
        self.offset = 0.0   # Scroll-Position in Entwurfs-Pixeln
        self.drag_from = None
        self.fetch_at = 0.0
        self.fetching = False
        self.scan()

    # -- Daten im Hintergrund holen, damit die Oberfläche nicht hängt --
    def tick(self):
        if not self.fetching and time.monotonic() >= self.fetch_at:
            self.fetching = True
            threading.Thread(target=self._fetch_thread, daemon=True).start()

    def _fetch_thread(self):
        try:
            items = self.fetch() if self.is_on() else []
        except Exception as exc:
            log("Abfrage fehlgeschlagen:", exc)
            items = self.items
        self.items, self.loaded = items, True
        self._fix_focus()
        self.fetch_at = time.monotonic() + 3
        self.fetching = False
        self.cc.changed = True

    def refetch(self, delay=1.5):
        self.fetch_at = time.monotonic() + delay

    def close(self):
        pass

    # -- Bedienung --
    def header(self):
        return ["back", "switch", "scan"]

    def nav(self, dx, dy):
        self._fix_focus()
        if dy:
            f = self.focus + dy
            while 0 < f <= len(self.items) and self.items[f - 1].get("header"):
                f += dy                       # Überschriften überspringen
            if f > len(self.items):
                f = self.focus
            self.focus = max(0, f)
            self.col = 0 if self.focus else min(self.col, 2)
            if self.focus:   # Fokus sichtbar halten (samt Überschrift darüber)
                top = (self.focus - 1) * self.ROW
                self.offset = min(max(self.offset, top + self.ROW - self.LIST_H), top)
                self._clamp()
            return
        n = 3 if self.focus == 0 else len(self.actions_of(self.focus - 1))
        self.col = max(0, min(n - 1, self.col + dx))

    def confirm(self):
        self._fix_focus()
        if self.focus == 0:
            self.tap(("sub", self.header()[self.col]))
        else:
            acts = self.actions_of(self.focus - 1)
            if acts:
                self.do(self.items[self.focus - 1], acts[min(self.col, len(acts) - 1)])

    @staticmethod
    def sectioned(groups):
        """[(Überschrift, [Einträge]), …] → flache Liste mit Überschriften (leere Gruppen weg)."""
        out = []
        for title, entries in groups:
            if entries:
                out.append({"key": "#" + title, "name": title, "header": True})
                out.extend(entries)
        return out

    def actions_of(self, idx):
        item = self.items[idx]
        return [] if item.get("header") else self.actions(item)

    def searching(self):
        return False

    def scan_label(self):
        if self.searching():
            return "Sucht …"
        return "Aktualisieren" if self.loaded else "Suchen"

    def _fix_focus(self):
        """Liste kann sich ändern (z. B. Gerät entfernt): Auswahl gültig halten."""
        self.focus = min(self.focus, len(self.items))
        if self.focus and self.items[self.focus - 1].get("header"):
            # auf eine Überschrift gerutscht: nächsten echten Eintrag nehmen, sonst den davor
            after = [i for i in range(self.focus, len(self.items)) if not self.items[i].get("header")]
            before = [i for i in range(self.focus - 1) if not self.items[i].get("header")]
            self.focus = after[0] + 1 if after else before[-1] + 1 if before else 0
        if self.focus:
            self.col = min(self.col, max(0, len(self.actions_of(self.focus - 1)) - 1))

    def _clamp(self):
        self.offset = max(0.0, min(max(0.0, len(self.items) * self.ROW - self.LIST_H), self.offset))

    # Finger ziehen = Liste scrollen (wie am Handy)
    def drag_start(self):
        self.drag_from = self.offset

    def drag(self, dy):
        if self.drag_from is not None:
            self.offset = self.drag_from - dy
            self._clamp()

    def tap(self, hit):
        kind = hit[0]
        if kind == "sub" and hit[1] == "back":
            self.cc.back()
        elif kind == "sub" and hit[1] == "switch":
            self.toggle()
            self.items = []
            self.refetch(4)
        elif kind == "sub" and hit[1] == "scan":
            if self.is_on():
                self.scan()
        elif kind == "subact":
            idx, act = hit[1], hit[2]
            if idx < len(self.items):
                self.focus = idx + 1
                acts = self.actions_of(idx)
                self.col = acts.index(act) if act in acts else 0
                self.do(self.items[idx], act)

    # -- Zeichnen --
    def draw(self, P):
        cc, T, A = self.cc, self.cc.T, self.cc.accent
        on = self.is_on()
        heads = [("back", 45, 170, "Zurück"),
                 ("switch", 1215 - 150 - 14 - 190, 150, "An" if on else "Aus"),
                 ("scan", 1215 - 190, 190, self.scan_label())]
        for n, (key, x, w, label) in enumerate(heads):
            if key == "scan" and not on:
                continue
            fill = A if key == "switch" and on else mix(T["tile"], A, 0.22) if key == "switch" else T["pill"]
            P.rrect(x, 62, w, 62, 31, fill)
            tc = "ffffff" if key == "switch" and on else T["text"]
            if key == "back":
                P.chevron(x + 30, 93, -9, tc)   # negative Größe = Pfeil nach links
            P.text(label, 20, x + w / 2 + (12 if key == "back" else 0), 100, tc, bold=True, align="c")
            if self.focus == 0 and self.col == n:
                cc._focus_ring(P, x, 62, w, 62, 31)
            cc.hits.append((x, 58, w, 70, ("sub", key)))

        P.text(self.title, 40, 240, 108, T["text"], bold=True)
        P.text(self.status_line() if on else f"{self.title} ist aus", 19, 45, 172, T["muted"])

        P.rrect(45, 195, 1170, self.LIST_H + 20, 24, T["card"])
        if not on:
            P.text(f"{self.title} einschalten, um {self.what} zu sehen", 22, 630, 500, T["muted"], align="c")
        elif not self.items:
            P.text("Suche läuft …" if not self.loaded or self.msg else f"Keine {self.what} gefunden",
                   22, 630, 500, T["muted"], align="c")
        self._clamp()
        P.clip(45, self.LIST_Y - 6, 1170, self.LIST_H + 12)
        first = int(self.offset // self.ROW)
        for idx in range(first, min(len(self.items), first + self.VISIBLE + 1)):
            item = self.items[idx]
            ry = self.LIST_Y + idx * self.ROW - self.offset
            if item.get("header"):      # Bereichsüberschrift
                P.text(tr(item["name"]).upper(), 16, 80, ry + 66, T["muted"], bold=True, raw=True)
                P.rrect(80, ry + 80, 1110, 2, 1, mix(T["muted"], T["card"], 0.6))
                continue
            if self.focus == idx + 1:
                P.rrect(57, ry, 1146, 90, 16, T["focus"])
            if item.get("highlight"):
                P.circle(85, ry + 45, 8, A)
            P.text(item["name"][:30], 23, 110, ry + 42, T["text"], bold=True, raw=True)
            P.text(self.describe(item), 17, 110, ry + 70, T["muted"])
            x = 1191
            acts = self.actions(item)
            for a_i in range(len(acts) - 1, -1, -1):
                act = acts[a_i]
                w = P.width(act, 18, bold=True) + 44
                x -= w
                primary = a_i == 0
                P.rrect(x, ry + 19, w, 52, 26, A if primary else mix(T["tile"], A, 0.22))
                P.text(act, 18, x + w / 2, ry + 52, "ffffff" if primary else T["text"], bold=True, align="c")
                if self.focus == idx + 1 and self.col == a_i:
                    cc._focus_ring(P, x, ry + 19, w, 52, 26)
                if self.LIST_Y - 10 <= ry + 19 and ry + 71 <= self.LIST_Y + self.LIST_H + 10:
                    cc.hits.append((x, ry + 10, w, 70, ("subact", idx, act)))
                x -= 12
        P.unclip()
        total = len(self.items) * self.ROW
        if total > self.LIST_H:   # Scrollbalken
            bar_h = max(60, self.LIST_H * self.LIST_H / total)
            bar_y = self.LIST_Y + (self.LIST_H - bar_h) * self.offset / (total - self.LIST_H)
            P.rrect(1203, bar_y, 6, bar_h, 3, mix(T["muted"], A, 0.4))
            count = sum(1 for i in self.items if not i.get("header"))
            P.text(f"{count} {self.what}  ·  mit dem Finger scrollen", 17, 630, 835,
                   T["muted"], align="c")
        cc.hits.append((45, 195, 1170, self.LIST_H + 20, ("sublist",)))
        P.text("A Auswählen", 17, 45, 835, T["muted"])
        P.text("B Zurück", 17, 1215, 835, T["muted"], align="r")


class WifiMenu(SubMenu):
    title = "WLAN"
    what = "Netze"

    def is_on(self):
        return bool(self.cc.wifi[0])

    def toggle(self):
        self.cc.press_tile(0)

    def scan(self):
        spawn(["nmcli", "dev", "wifi", "rescan"])
        self.msg = "Suche nach Netzen …"
        self.scan_until = time.monotonic() + 3
        self.refetch(2.5)

    def searching(self):
        return time.monotonic() < getattr(self, "scan_until", 0)

    def status_line(self):
        ssid = self.cc.wifi[1]
        return self.msg or (f"Verbunden mit {ssid}" if ssid else "Nicht verbunden")

    def saved_networks(self):
        """SSID -> Name der gespeicherten Verbindung (Name und SSID können abweichen)."""
        con = run(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"], timeout=4) or ""
        saved = {}
        for f in map(nmcli_split, con.splitlines()):
            if len(f) > 1 and "wireless" in f[1]:
                ssid = (run(["nmcli", "-g", "802-11-wireless.ssid", "connection", "show", "id", f[0]],
                            timeout=3) or "").strip() or f[0]
                saved[ssid] = f[0]
        return saved

    def fetch(self):
        out = run(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "dev", "wifi", "list"], timeout=6) or ""
        saved = self.saved_networks()
        items, seen = [], set()
        for line in out.splitlines():
            f = nmcli_split(line)
            if len(f) < 4 or not f[1] or f[1] in seen:
                continue
            seen.add(f[1])
            items.append({"key": f[1], "name": f[1], "active": f[0] == "*", "saved": f[1] in saved,
                          "con": saved.get(f[1]), "near": True,
                          "signal": int(f[2]) if f[2].isdigit() else 0,
                          "secure": f[3] not in ("", "--"), "highlight": f[0] == "*"})
        for ssid, con in saved.items():      # gespeichert, aber gerade nicht in Reichweite
            if ssid not in seen:
                items.append({"key": ssid, "name": ssid, "active": False, "saved": True, "con": con,
                              "near": False, "signal": 0, "secure": True, "highlight": False})
        # verbunden → gespeichert (in Reichweite) → gespeichert (fern) → Rest nach Signal
        items.sort(key=lambda i: (not i["active"], not i["saved"], not i["near"], -i["signal"]))
        self.msg = ""
        return self.sectioned([("Gespeicherte Netze", [i for i in items if i["saved"]]),
                               ("Weitere Netze", [i for i in items if not i["saved"]])])

    def describe(self, it):
        if not it["near"]:
            return "Gespeichert · nicht in Reichweite"
        state = "Verbunden" if it["active"] else "Gespeichert" if it["saved"] else \
            "Gesichert" if it["secure"] else "Offen"
        return f"{state} · Signal {it['signal']} %"

    def actions(self, it):
        if it["active"]:
            return ["Trennen"]
        if it["saved"]:
            return ["Verbinden", "Vergessen"] if it["near"] else ["Vergessen"]
        return ["Passwort …"] if it["secure"] else ["Verbinden"]

    def do(self, it, act):
        ssid = it["name"]
        prof = ". /etc/profile; "
        if act == "Verbinden" and it["saved"]:
            # gespeicherte Verbindung einfach wieder aufbauen; klappt das nicht und ist es das
            # ROCKNIX-Standardnetz, verbindet wifictl mit den gespeicherten Zugangsdaten
            script = (prof + 'nmcli -w 30 connection up id "$2" || '
                      '{ [ "$(get_setting wifi.ssid)" = "$1" ] && wifictl connect; } && '
                      'set_setting wifi.ssid "$1" && '
                      'set_setting wifi.key "$(nmcli -s -g 802-11-wireless-security.psk connection show id "$2")"')
        elif act == "Verbinden":
            script = prof + 'nmcli dev wifi connect "$1" && set_setting wifi.ssid "$1" && set_setting wifi.key ""'
        elif act == "Trennen":
            script = 'nmcli dev disconnect "$(ls /sys/class/net | grep -m1 ^wlan)"'
        elif act == "Vergessen":
            script = 'nmcli connection delete id "$2"'
        else:
            self.cc.kbd = Keyboard(self.cc, f"Passwort für {ssid}",
                                   lambda pw: self.connect_new(ssid, pw))
            return
        log("WLAN:", act, ssid)
        spawn(["bash", "-c", script, "rds", ssid, it.get("con") or ssid])
        self.msg = {"Verbinden": f"Verbinde mit {ssid} …", "Trennen": "Trenne …",
                    "Vergessen": f"{ssid} vergessen"}[act]
        self.cc.status_at = time.monotonic() + 3
        self.refetch(4)


    def connect_new(self, ssid, pw):
        if not pw:
            return
        log("WLAN: Verbinden (neu)", ssid)          # Passwort nie ins Log
        script = ('. /etc/profile; nmcli connection delete id "$1" >/dev/null 2>&1; '
                  'nmcli -w 60 dev wifi connect "$1" password "$2" && '
                  'set_setting wifi.ssid "$1" && set_setting wifi.key "$2"')
        spawn(["bash", "-c", script, "rds", ssid, pw])
        self.msg = f"Verbinde mit {ssid} …"
        self.cc.status_at = time.monotonic() + 6
        self.refetch(6)


class BtMenu(SubMenu):
    """Bluetooth über ROCKNIX' eigenen Weg (rocknix-bluetooth + Bluetooth-Helfer).

    Der Helfer (bluetooth-agent) sucht, koppelt, vertraut und verbindet selbst;
    `rocknix-bluetooth trust` sichert die Kopplung danach, damit sie einen Neustart übersteht.
    """
    title = "Bluetooth"
    what = "Geräte"
    CONTROL = "/run/bt_discovery_control"
    WANTED = "/run/bt_device"         # Gerät, das der Helfer koppeln/verbinden soll
    STATUS = "/run/bt_status"
    SCAN_TIME = 60

    def __init__(self, cc):
        self.scan_until = 0.0
        self.msg_until = 0.0
        super().__init__(cc)

    def is_on(self):
        return bool(self.cc.bt[0])

    def toggle(self):
        self.cc.press_tile(1)

    def scan(self):
        if not self.is_on():
            return
        wr(self.CONTROL, "start")          # Suche über den ROCKNIX-Helfer
        self.scan_until = time.monotonic() + self.SCAN_TIME
        self.refetch(2)

    def searching(self):
        return bool(self.scan_until) and time.monotonic() < self.scan_until

    def close(self):
        """Suche beenden und den Koppel-Wunsch löschen (wie das ES-Menü beim Verlassen)."""
        if self.scan_until:
            wr(self.CONTROL, "stop")
            self.scan_until = 0.0
        try:
            os.remove(self.WANTED)
        except OSError:
            pass

    def tick(self):
        if self.scan_until and time.monotonic() > self.scan_until:
            self.close()
        super().tick()

    def status_line(self):
        helper = rd(self.STATUS) or ""
        if helper and time.monotonic() < self.msg_until + 30:
            return helper                   # Meldung des Helfers, z. B. „Pairing …“
        if self.msg and time.monotonic() < self.msg_until:
            return self.msg
        left = int(self.scan_until - time.monotonic()) if self.scan_until else 0
        return f"Suche nach Geräten … noch {left} s – Controller in den Kopplungsmodus versetzen" \
            if left > 0 else f"Tippe auf „{self.scan_label()}“, um neue Geräte zu finden"

    @staticmethod
    def _devices(*args):
        out = run(["bluetoothctl", "devices", *args], timeout=4) or ""
        res = {}
        for line in out.splitlines():
            parts = line.split(" ", 2)
            if len(parts) >= 2 and parts[0] == "Device":
                res[parts[1]] = parts[2] if len(parts) > 2 else parts[1]
        return res

    def fetch(self):
        alld, paired, conn = self._devices(), self._devices("Paired"), self._devices("Connected")
        items = []
        for mac, name in alld.items():
            if name.replace("-", ":") == mac:
                continue   # Geräte ohne Namen weglassen
            icon = ""
            if mac in paired:   # Gerätetyp nur für gekoppelte Geräte abfragen (wenige, schnell)
                info = run(["bluetoothctl", "info", mac], timeout=3) or ""
                m = re.search(r"Icon:\s*(\S+)", info)
                icon = m.group(1) if m else ""
            items.append({"key": mac, "name": name, "mac": mac, "paired": mac in paired,
                          "connected": mac in conn, "highlight": mac in conn,
                          "input": icon.startswith("input")})
        items.sort(key=lambda i: (not i["connected"], not i["paired"], i["name"].lower()))
        return self.sectioned([("Gekoppelte Geräte", [i for i in items if i["paired"]]),
                               ("Gefundene Geräte", [i for i in items if not i["paired"]])])

    def describe(self, it):
        state = "Verbunden" if it["connected"] else "Gekoppelt" if it["paired"] else "Neu"
        if it.get("input") and it["connected"]:
            state += " · trennen: Controller ausschalten"
        return state + " · " + it["mac"]

    def actions(self, it):
        if it["connected"]:
            # Controller verbinden sich von selbst neu → getrennt wird durch Ausschalten
            return ["Entfernen"] if it.get("input") else ["Trennen", "Entfernen"]
        if it["paired"]:
            return ["Verbinden", "Entfernen"]
        return ["Koppeln"]

    def do(self, it, act):
        mac = it["mac"]
        if act == "Koppeln" and not self.scan_until:
            self.scan()                    # der Helfer koppelt nur während der Suche
        if act in ("Trennen", "Entfernen"):
            self.close()                   # sonst verbindet der Helfer das Gerät sofort neu
        cmd = {"Koppeln": "trust", "Verbinden": "connect", "Trennen": "disconnect",
               "Entfernen": "remove"}[act]
        log("Bluetooth:", act, it["name"], mac)
        spawn(["rocknix-bluetooth", cmd, mac])
        self.msg = {"Koppeln": f"Kopple {it['name']} … (bis zu 60 s)",
                    "Verbinden": f"Verbinde {it['name']} …",
                    "Trennen": f"{it['name']} getrennt – zum dauerhaften Trennen Controller ausschalten",
                    "Entfernen": f"{it['name']} entfernt"}[act]
        self.msg_until = time.monotonic() + 8
        self.cc.status_at = time.monotonic() + 3
        self.refetch(3)


# ------------------------------------------------------- Bildschirmtastatur --

def _keyrow(chars):
    return [("char", c, 1) for c in chars]


KB_BOTTOM = [("layer", None, 1.5), ("char", ",", 1), ("space", None, 4), ("char", ".", 1), ("ok", None, 2.5)]
# wie am Handy: 10 Spalten, Umlaute und Sonderformen durch langes Drücken
KB_LAYERS = [
    [_keyrow("1234567890"), _keyrow("qwertzuiop"), _keyrow("asdfghjkl"),
     [("shift", None, 1.5)] + _keyrow("yxcvbnm") + [("back", None, 1.5)], KB_BOTTOM],
    [_keyrow("1234567890"), _keyrow("!@#$%&*()?"), _keyrow("-_+=/\\:;'\""),
     [("shift", None, 1.5)] + _keyrow("<>[]{}|") + [("back", None, 1.5)], KB_BOTTOM],
]
KB_QWERTY = [
    [_keyrow("1234567890"), _keyrow("qwertyuiop"), _keyrow("asdfghjkl"),
     [("shift", None, 1.5)] + _keyrow("zxcvbnm") + [("back", None, 1.5)], KB_BOTTOM],
    KB_LAYERS[1],
]
KB_OFFSET = [0, 0, 0.5, 0, 0]     # Reihe „asdf…“ halb eingerückt wie am Handy
KB_VARIANTS = {"a": "äàáâæ", "o": "öóòôø", "u": "üúùû", "s": "ß", "e": "éèêë€",
               "i": "íìîï", "n": "ñ", "c": "ç",
               "$": "€£¥", "-": "–~", "|": "~^`", "?": "¿", "!": "¡", ".": "…", "'": "`´"}
KB_GAP = 10
KB_UNIT = (1170 - 9 * KB_GAP) / 10
KB_HOLD = 0.45                   # Sekunden bis zum Varianten-Menü


def keyboard_layout(cfg):
    """QWERTZ für deutschsprachige Systeme, sonst QWERTY; per Einstellung überschreibbar."""
    forced = (cfg.get("keyboard") or "").lower()
    if forced in ("qwertz", "qwerty"):
        return forced
    lang = ""
    try:
        with open("/storage/.config/system/configs/system.cfg") as f:
            for line in f:
                if line.startswith("system.language="):
                    lang = line.split("=", 1)[1].strip().lower()
    except OSError:
        pass
    lang = lang or os.environ.get("LANG", "").lower()
    return "qwertz" if lang.startswith("de") else "qwerty"


class Keyboard:
    """Eigene Bildschirmtastatur (QWERTZ) für Touch und Gamepad."""

    def __init__(self, cc, title, on_ok, secret=True):
        self.cc, self.title, self.on_ok, self.secret = cc, title, on_ok, secret
        self.text, self.cur = "", 0
        self.shift = 0          # 0 aus, 1 einmal, 2 dauerhaft
        self.layer = 0
        self.show = not secret
        self.layers = KB_LAYERS if keyboard_layout(cc.cfg) == "qwertz" else KB_QWERTY
        self.r, self.c = 1, 0   # Fokus auf der Tastatur (-1 = Kopfzeile)
        self.hc = 0             # Spalte in der Kopfzeile: Abbrechen / Zeigen
        self.field = None       # (x0, Zeichenpositionen) fürs Antippen im Textfeld
        self.popup = None       # Varianten-Leiste beim langen Drücken
        self.hold = None        # (start, quelle, daten) für langes Drücken

    def rows(self):
        return self.layers[self.layer]

    def _label(self, kind, val):
        if kind == "char":
            return val.upper() if self.shift and val.isalpha() and val != "ß" else val
        return {"layer": "abc" if self.layer else "?123", "space": "Leerzeichen",
                "ok": "OK", "shift": "", "back": ""}[kind]

    # -- Aktionen --
    def press(self, kind, val):
        if kind == "char":
            self.insert(self._label(kind, val))
        elif kind == "space":
            self.press("char", " ")
        elif kind == "back":
            self.backspace()
        elif kind == "shift":
            self.toggle_shift()
        elif kind == "layer":
            self.toggle_layer()
        elif kind == "ok":
            self.ok()

    def variants(self, r, c):
        kind, val, _u = self.rows()[r][c]
        if kind != "char" or val not in KB_VARIANTS:
            return None
        return [self._label("char", v) if v != "ß" else v for v in KB_VARIANTS[val]]

    def open_popup(self, r, c, by_touch):
        var = self.variants(r, c)
        if var:
            self.popup = {"r": r, "c": c, "vars": var, "sel": 0, "touch": by_touch, "xs": []}
            self.r, self.c = r, c

    def insert(self, ch):
        self.text = self.text[:self.cur] + ch + self.text[self.cur:]
        self.cur += len(ch)
        if self.shift == 1:
            self.shift = 0

    def pick(self):
        if self.popup:
            self.insert(self.popup["vars"][self.popup["sel"]])
            self.popup = None

    def tick(self):
        """Langes Drücken erkennen (Touch oder A)."""
        if not self.hold or self.popup:
            return False
        start, src, data = self.hold
        if src.endswith("-used") or time.monotonic() - start < KB_HOLD:
            return False
        if src == "touch":
            hit = data
            if hit and hit[0] == "kb":
                self.open_popup(hit[1], hit[2], True)
        elif self.r >= 0:
            self.open_popup(self.r, self.c, False)
        self.hold = (start, src + "-used", data)
        return bool(self.popup)

    # Gamepad-A: Druck und Loslassen getrennt (langes Halten öffnet Varianten)
    def a_down(self):
        if self.popup:
            return
        self.hold = (time.monotonic(), "pad", None)

    def a_up(self):
        hold, self.hold = self.hold, None
        if self.popup:
            if hold and hold[1] == "pad-used":
                return               # gerade erst geöffnet: Auswahl folgt
            self.pick()
            return
        if hold and hold[1] == "pad-used":
            return                   # gehalten, aber Taste ohne Varianten
        self.confirm()

    # Touch: Finger halten → Varianten, ziehen → auswählen, loslassen → einfügen
    def touch_down(self, x, y):
        hit = self.cc._hit(x, y)
        self.hold = (time.monotonic(), "touch", hit)
        self.t_from = (x, y)

    def touch_move(self, x, y):
        if self.hold and not self.popup and (abs(x - self.t_from[0]) > 40 or abs(y - self.t_from[1]) > 40):
            self.hold = None         # Finger bewegt: kein langes Drücken
        if self.popup and self.popup["touch"] and self.popup["xs"]:
            xs = self.popup["xs"]
            self.popup["sel"] = min(range(len(xs)), key=lambda i: abs(xs[i] - x))

    def touch_up(self, x0, y0, x1, y1):
        hold, self.hold = self.hold, None
        if self.popup and self.popup["touch"]:
            self.pick()
            return
        if hold and hold[1] == "touch-used":
            return                   # gehalten auf Taste ohne Varianten
        if abs(x1 - x0) < 40 and abs(y1 - y0) < 40:
            hit = self.cc._hit(x0, y0)
            if hit:
                self.tap(hit, x0)

    def backspace(self):
        if self.cur > 0:
            self.text = self.text[:self.cur - 1] + self.text[self.cur:]
            self.cur -= 1

    def toggle_shift(self):
        self.shift = (self.shift + 1) % 3

    def toggle_layer(self):
        self.layer = 1 - self.layer
        self.c = min(self.c, len(self.rows()[self.r]) - 1) if self.r >= 0 else self.c

    def cursor(self, d):
        self.cur = max(0, min(len(self.text), self.cur + d))

    def ok(self):
        self.cc.kbd = None
        self.on_ok(self.text)

    def cancel(self):
        self.cc.kbd = None

    def back(self):
        """B: Varianten schließen, sonst letztes Zeichen löschen; bei leerem Feld abbrechen."""
        if self.popup:
            self.popup = None
        elif self.text:
            self.backspace()
        else:
            self.cancel()

    # -- Gamepad --
    def _centers(self, r):
        x, out = 45 + KB_OFFSET[r] * (KB_UNIT + KB_GAP), []
        for _k, _v, units in self.rows()[r]:
            w = units * KB_UNIT + (units - 1) * KB_GAP
            out.append(x + w / 2)
            x += w + KB_GAP
        return out

    def nav(self, dx, dy):
        if self.popup:
            if dx:
                self.popup["sel"] = max(0, min(len(self.popup["vars"]) - 1, self.popup["sel"] + dx))
            return
        if dy:
            if self.r == -1:
                if dy > 0:
                    self.r, self.c = 0, 0 if self.hc == 0 else len(self.rows()[0]) - 1
                return
            nr = self.r + dy
            if nr < 0:
                self.r = -1
                self.hc = 0 if self._centers(self.r + 1)[self.c] < 630 else 1
                return
            if nr >= len(self.rows()):
                return
            cx = self._centers(self.r)[self.c]
            centers = self._centers(nr)
            self.r, self.c = nr, min(range(len(centers)), key=lambda i: abs(centers[i] - cx))
        elif self.r == -1:
            self.hc = max(0, min(1, self.hc + dx))
        else:
            self.c = max(0, min(len(self.rows()[self.r]) - 1, self.c + dx))

    def confirm(self):
        if self.r == -1:
            self.cancel() if self.hc == 0 else setattr(self, "show", not self.show)
        else:
            kind, val, _u = self.rows()[self.r][self.c]
            self.press(kind, val)

    # -- Touch --
    def tap(self, hit, x=None):
        kind = hit[0]
        if kind == "kb_var" and self.popup:
            self.popup["sel"] = hit[1]
            self.pick()
            return
        self.popup = None
        if kind == "kb":
            r, c = hit[1], hit[2]
            self.r, self.c = r, c
            k, v, _u = self.rows()[r][c]
            self.press(k, v)
        elif kind == "kb_cancel":
            self.cancel()
        elif kind == "kb_show":
            self.show = not self.show
        elif kind == "kb_field" and x is not None and self.field:
            x0, pos = self.field
            self.cur = min(range(len(pos)), key=lambda i: abs(x0 + pos[i] - x))

    # -- Zeichnen --
    def draw(self, P):
        cc, T, A = self.cc, self.cc.T, self.cc.accent
        hits = cc.hits
        # Kopfzeile
        for n, (key, x, w, label) in enumerate([("kb_cancel", 45, 190, "Abbrechen"),
                                                ("kb_show", 1215 - 190, 190, "Verbergen" if self.show else "Zeigen")]):
            if key == "kb_show" and not self.secret:
                continue
            P.rrect(x, 62, w, 62, 31, T["pill"])
            P.text(label, 20, x + w / 2, 100, T["text"], bold=True, align="c")
            if self.r == -1 and self.hc == n:
                cc._focus_ring(P, x, 62, w, 62, 31)
            hits.append((x, 58, w, 70, (key,)))
        P.text(self.title[:34], 26, 630, 102, T["text"], bold=True, align="c")

        # Textfeld mit Cursor
        P.rrect(45, 148, 1170, 92, 20, T["card"])
        P.rrect(45, 148, 1170, 92, 20, A, stroke=3)
        hidden = self.secret and not self.show
        pos = [0.0]
        for i in range(len(self.text)):
            pos.append(pos[-1] + (26 if hidden else P.width(self.text[i], 30, raw=True)))
        shift = max(0, pos[self.cur] - 1080)       # langer Text: mitlaufen
        x0 = 75 - shift
        if hidden:
            for i in range(len(self.text)):
                cx = x0 + pos[i] + 13
                if 60 < cx < 1200:
                    P.circle(cx, 194, 7, T["text"])
        else:
            vis_start = next((i for i in range(len(pos)) if x0 + pos[i] >= 60), 0)
            P.text(self.text[vis_start:], 30, x0 + pos[vis_start], 205, T["text"], raw=True)
        if not self.text:
            P.text("Passwort eingeben" if self.secret else "Text eingeben", 26, 75, 204, T["muted"])
        P.rrect(x0 + pos[self.cur] - 1, 170, 3, 48, 1.5, A)
        self.field = (x0, pos)
        hits.append((45, 148, 1170, 92, ("kb_field",)))

        # Tasten
        for r, row in enumerate(self.rows()):
            x, y = 45 + KB_OFFSET[r] * (KB_UNIT + KB_GAP), 268 + r * 102
            for c, (kind, val, units) in enumerate(row):
                w = units * KB_UNIT + (units - 1) * KB_GAP
                special = kind != "char"
                active = (kind == "shift" and self.shift) or kind == "ok"
                fill = A if active else mix(T["tile"], A, 0.30 if special else 0.12)
                tc = "ffffff" if active else T["text"]
                P.rrect(x, y, w, 92, 16, fill)
                if kind == "shift":   # Pfeil nach oben, bei Dauer-Großschreibung mit Strich
                    cx = x + w / 2
                    cairo.cairo_new_path(P.cr)
                    cairo.cairo_move_to(P.cr, P.X(cx - 14), P.Y(y + 50))
                    cairo.cairo_line_to(P.cr, P.X(cx), P.Y(y + 32))
                    cairo.cairo_line_to(P.cr, P.X(cx + 14), P.Y(y + 50))
                    cairo.cairo_move_to(P.cr, P.X(cx), P.Y(y + 33))
                    cairo.cairo_line_to(P.cr, P.X(cx), P.Y(y + 60))
                    if self.shift == 2:
                        cairo.cairo_move_to(P.cr, P.X(cx - 12), P.Y(y + 68))
                        cairo.cairo_line_to(P.cr, P.X(cx + 12), P.Y(y + 68))
                    cairo.cairo_set_line_width(P.cr, 4 * P.s)
                    cairo.cairo_set_line_cap(P.cr, 1)
                    P.color(tc)
                    cairo.cairo_stroke(P.cr)
                elif kind == "back":  # Rücktaste: Pfeil nach links
                    cx = x + w / 2
                    P.chevron(cx - 6, y + 46, -11, tc)
                    cairo.cairo_new_path(P.cr)
                    cairo.cairo_move_to(P.cr, P.X(cx - 16), P.Y(y + 46))
                    cairo.cairo_line_to(P.cr, P.X(cx + 18), P.Y(y + 46))
                    cairo.cairo_stroke(P.cr)
                else:
                    label = self._label(kind, val)
                    P.text(label, 32 if kind == "char" else 21, x + w / 2, y + 58, tc,
                           bold=kind != "char", align="c")
                    var = self.variants(r, c)
                    if var:   # wichtigste Variante klein in der Ecke
                        P.text(var[0], 15, x + w - 12, y + 24, T["muted"], align="r")
                if self.r == r and self.c == c:
                    cc._focus_ring(P, x, y, w, 92, 16)
                hits.append((x, y, w, 92, ("kb", r, c)))
                x += w + KB_GAP

        if self.popup:
            pp = self.popup
            n = len(pp["vars"])
            bw, cx = 92, self._centers(pp["r"])[pp["c"]]
            width = n * bw + (n - 1) * 8 + 24
            px = max(45, min(1215 - width, cx - width / 2))
            py = 268 + pp["r"] * 102 - 118
            P.rrect(px - 3, py - 3, width + 6, 116, 22, A)      # Rahmen in Akzentfarbe
            P.rrect(px, py, width, 110, 20, T["card"])
            pp["xs"] = []
            for i, v in enumerate(pp["vars"]):
                bx = px + 12 + i * (bw + 8)
                sel = i == pp["sel"]
                P.rrect(bx, py + 9, bw, 92, 14, A if sel else mix(T["tile"], A, 0.12))
                P.text(v, 32, bx + bw / 2, py + 67, "ffffff" if sel else T["text"], align="c")
                pp["xs"].append(bx + bw / 2)
                hits.insert(0, (bx, py + 9, bw, 92, ("kb_var", i)))
        hint = ("Links/Rechts wählen · A einfügen · B schließen" if self.popup else
                "A Taste (halten: ä, ö, ü …) · B Löschen · L1 Groß · R1 ?123 · Stick Cursor · Start OK")
        P.text(hint, 17, 630, 835, T["muted"], align="c")



class ControlCenter:
    """Zustand, Zeichnen und Bedienung des Kontrollcenters."""

    def __init__(self):
        self.cfg = load_config()
        LANG[0] = ui_language()
        self.T = THEMES.get(self.cfg.get("theme"), THEMES["dark"])
        self.accent = (self.cfg.get("accent") or "#e5383b").lstrip("#")
        self.backlights = find_backlights(self.cfg)
        log("Regler:", ", ".join(f"{label} = {b.name}" for label, b in self.backlights) or "keine Helligkeit gefunden")
        self.page = 0
        self.focus = 1          # Zeile auf Seite 1 (0 = Darstellung oben)
        self.top_sel = 0        # -1 = Power, 0 = Hell/Dunkel, 1 = Akzentfarbe
        self.tile = 0           # Spalte in der Kachelzeile
        self.values = {}
        self.perf = 1
        self.perf_sel = 1       # Auswahl mit links/rechts, übernommen mit A
        self.wifi = (None, None)
        self.bt = (False, [])
        self.screen_bottom_off = False
        self.screen_bottom_saved = None   # gespeicherte Helligkeit vor dem Ausschalten
        self.screen_auto = False          # automatisch gedimmt (RetroArch-Start)
        self.bat = (None, False)
        self.game = None
        self.marquee = False
        self.marquee_t0 = 0.0
        self.switcher = Switcher()
        self.loading = None   # (Eintrag, neu_starten) während eines Wechsels
        self.hits = []          # (x, y, w, h, aktion) in Entwurfs-Koordinaten
        self.tracks = {}        # Regler -> (x0, x1)
        self.touch = None
        self.drag = None
        self.vol_sent = 0.0
        self.status_at = 0.0
        self.pen = None
        self.sub = None         # geöffnetes Untermenü (WLAN/Bluetooth)
        self.kbd = None         # geöffnete Bildschirmtastatur
        self.changed = False    # Hintergrund-Abfrage hat neue Daten
        self.power_menu = PowerMenu(self)
        self.power_hits = []    # Touch-Ziele des Power-Menüs

    # -- Daten --
    def rows(self):
        r = [("top", None)] + ([("game", None)] if self.game else []) \
            + [("slider", i) for i in range(len(self.backlights))] + [("slider", "vol")]
        return r + [("perf", None), ("tiles", None)]

    def refresh(self, full=False):
        if full:
            LANG[0] = ui_language()   # ES-Sprache gewechselt → beim nächsten Öffnen übernehmen
            for i, (_label, b) in enumerate(self.backlights):
                self.values[i] = b.get()
            v = volume_get()
            self.values["vol"] = v if v is not None else self.values.get("vol", 50)
            self.perf = self.perf_sel = perf_get()
            self.game = running_game()
            self.marquee_t0 = time.monotonic()
            rows = self.rows()
            self.focus = min(self.focus, len(rows) - 1)
            if rows[self.focus][0] == "game":   # nie versehentlich auf „Beenden“ starten
                self.focus += 1
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

    def toggle_theme(self):
        name = "light" if self.T is THEMES["dark"] else "dark"
        self.T = THEMES[name]
        self.cfg["theme"] = name
        save_config(self.cfg)

    def next_accent(self):
        i = ACCENTS.index(self.accent) if self.accent in ACCENTS else -1
        self.accent = ACCENTS[(i + 1) % len(ACCENTS)]
        self.cfg["accent"] = "#" + self.accent
        save_config(self.cfg)

    def open_sub(self, i):
        self.sub = (WifiMenu if i == 0 else BtMenu)(self)
        log("Untermenü:", self.sub.title)

    def reset(self):
        """Beim Schließen des Overlays: Tastatur und Untermenü verlassen."""
        self.kbd = None
        self.back()

    def back(self):
        """B: Tastatur/Untermenü zurück. Liefert True, wenn das Kontrollcenter offen bleibt."""
        if self.kbd:
            self.kbd.back()
            return True
        if self.sub:
            self.sub.close()
            self.sub = None
            return True
        return False

    def tick(self):
        if self.kbd and self.kbd.tick():
            self.changed = True
        if self.sub:
            self.sub.tick()

    def details(self):
        if self.page == 0 and not self.sub and self.rows()[self.focus][0] == "tiles" and self.tile < 2:
            self.open_sub(self.tile)

    def press_tile(self, i):
        if i == 0:
            on = not self.wifi[0]
            if wifi_set(on):
                self.wifi = (on, self.wifi[1] if on else None)
                self.status_at = time.monotonic() + 5  # Verbindungsaufbau abwarten
        elif i == 1:
            on = not self.bt[0]
            if bt_set(on):
                self.bt = (on, self.bt[1] if on else [])
                self.status_at = time.monotonic() + 2   # Dienststart abwarten
        elif i == 2:
            if not self.screen_bottom_off:
                self.screen_off()
                return "close"   # CC schließen, System bleibt bedienbar
            self.screen_on()
        elif i == 3:
            log("Ruhemodus")
            subprocess.Popen(["systemctl", "suspend"])

    def _bl_bottom(self):
        return next((b for label, b in self.backlights if "unten" in label.lower()), None)

    def screen_off(self):
        """Unteren Bildschirm dunkel schalten (Helligkeit merken)."""
        if self.screen_bottom_off:
            return
        bl = self._bl_bottom()
        if bl:
            self.screen_bottom_saved = bl.get()
            bl.set(0, allow_off=True)
        self.screen_bottom_off = True
        log("Unterer Screen: aus")

    def screen_on(self):
        """Ursprüngliche Helligkeit wiederherstellen."""
        if not self.screen_bottom_off:
            return
        bl = self._bl_bottom()
        if bl:
            bl.set(self.screen_bottom_saved or 50)
        self.screen_bottom_saved = None
        self.screen_bottom_off = False
        self.screen_auto = False
        log("Unterer Screen: an")

    # -- Bedienung mit Tasten --
    def nav(self, dx, dy):
        if self.kbd:
            self.kbd.nav(dx, dy)
            return
        if self.sub:
            self.sub.nav(dx, dy)
            return
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
        elif kind == "top":
            self.top_sel = max(-1, min(1, self.top_sel + dx))

    def confirm(self):
        if self.kbd:
            self.kbd.confirm()
            return
        if self.sub:
            self.sub.confirm()
            return
        if self.page != 0:
            return
        kind = self.rows()[self.focus][0]
        if kind == "tiles":
            return self.press_tile(self.tile)
        elif kind == "perf":
            self.set_perf(self.perf_sel)
        elif kind == "game":
            return "quit"
        elif kind == "top":
            if self.top_sel == -1:
                return "power"
            self.toggle_theme() if self.top_sel == 0 else self.next_accent()

    def turn_page(self, d):
        if self.sub:
            return
        self.page = max(0, min(len(PAGES) - 1, self.page + d))

    # -- Bedienung mit Touch (Pixel des Bildschirms) --
    def touch_down(self, px, py):
        if not self.pen:
            return
        x, y = self.pen.to_design(px, py)
        self.touch = (x, y, x, y)
        if self.kbd:
            self.kbd.touch_down(x, y)
            return
        if self.sub:
            self.sub.drag_start()
            return
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
        if self.kbd:
            self.kbd.touch_move(x, y)
            return
        if self.sub:
            dy = y - self.touch[1]
            if abs(dy) > 15:
                self.sub.drag(dy)
            return
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
        if self.kbd:
            self.kbd.touch_up(x0, y0, x1, y1)
            return
        if self.sub:
            self.sub.drag_from = None
            if abs(dx) < 30 and abs(dy) < 15:
                hit = self._hit(x0, y0)
                if hit and hit[0] != "sublist":
                    self.sub.tap(hit)
            return
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
                return self.press_tile(val)
            elif kind == "more":
                self.focus, self.tile = self.rows().index(("tiles", None)), val
                self.open_sub(val)
            elif kind == "page":
                self.page = val
            elif kind == "top":
                self.focus, self.top_sel = 0, val
                self.toggle_theme() if val == 0 else self.next_accent()
            elif kind == "power_btn":
                return "power"
            elif kind == "quit":
                return "quit"

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
        if view == "power":
            self.power_hits = self.power_menu.draw(P, T, self.accent)
            return
        if view == "switcher":
            self._draw_switcher(P)
            return
        elif view == "loading":
            self._draw_loading(P)
            return
        if self.kbd:
            self.kbd.draw(P)
            return
        if self.sub:
            pass
        elif self.page == 0:
            self._draw_quick(P)
        else:
            self._draw_placeholder(P)
        # Fußzeile mit Seitenpunkten
        if self.sub:
            self.sub.draw(P)
            return
        left = "L1 / R1 Seite wechseln"
        if self.page == 0 and self.rows()[self.focus][0] == "tiles" and self.tile < 2:
            left = "A Ein/Aus  ·  X / Y Details"
        P.text(left, 17, 45, 835, T["muted"])
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
        date = f"{WEEKDAYS[now.tm_wday]}, {now.tm_mday}. {MONTHS[now.tm_mon - 1]}"
        P.text(date, 19, 45, 118, T["muted"])
        left_end = 45 + max(P.width(date, 19), P.width(time.strftime("%H:%M", now), 52, bold=True))

        # Status-Pillen rechts oben
        cap, charging = self.bat
        pills = [(f"Akku {cap} %" if cap is not None else "Akku ?") + (" · lädt" if charging else "")]
        x = 1215
        for label in reversed(pills):
            wdt = P.width(label, 19, bold=True) + 48
            x -= wdt
            P.rrect(x, 70, wdt, 54, 27, T["pill"])
            P.text(label, 19, x + 24, 104, T["text"], bold=True)
            x -= 14

        # Darstellung: Hell/Dunkel und Akzentfarbe
        top_focus = self.rows()[self.focus][0] == "top"
        for i in (1, 0):
            x -= 54
            cx = x + 27
            P.circle(cx, 97, 27, T["pill"])
            if i == 0:   # Mond (Dunkel) bzw. Sonne mit Strahlen (Hell)
                if self.T is THEMES["dark"]:
                    P.circle(cx, 97, 12, T["text"])
                    P.circle(cx + 6, 92, 10, T["pill"])
                else:
                    P.sun(cx, 97, T["text"])
            else:
                P.circle(cx, 97, 13, A)
            if top_focus and self.top_sel == i:
                self._focus_ring(P, x, 70, 54, 54, 27)
            self.hits.append((x - 4, 66, 62, 62, ("top", i)))
            x -= 14

        # Power-Kreis ganz rechts in der Kopfzeile
        x -= 54
        pcx = x + 27
        P.circle(pcx, 97, 27, T["pill"])
        P.power_icon(pcx, 97, 14, T["text"], width=3)
        if top_focus and self.top_sel == -1:
            self._focus_ring(P, x, 70, 54, 54, 27)
        self.hits.append((x - 4, 66, 62, 62, ("power_btn", None)))
        x -= 14

        # Titel mit Logo mittig zwischen Datum und rechter Gruppe (passt sich der Sprache an)
        room_l, room_r = left_end + 24, x - 10
        size = 38
        while size > 26 and P.width("Kontrollcenter", size, bold=True) + 16 + size * 1.37 * 230 / 130 > room_r - room_l:
            size -= 2
        lh = size * 1.37
        lw = 230 * lh / 130
        tw = P.width("Kontrollcenter", size, bold=True)
        lx = max(room_l, (room_l + room_r) / 2 - (lw + 16 + tw) / 2)
        P.logo(lx, 97 - lh / 2, lh, T["text"], T["bg"])
        P.text("Kontrollcenter", size, lx + lw + 16, 97 + size * 0.36, T["text"], bold=True)

        # Läuft gerade
        P.rrect(45, 145, 1170, 135, 24, T["card"])
        icon = self.game.get("icon") if self.game else None
        if not (icon and P.image(icon, 72, 167, 90, 90, 14)):
            P.rrect(72, 167, 90, 90, 14, T["tile"])
            P.text((self.game["name"][:1] if self.game else "–").upper(), 40, 117, 227, T["muted"], bold=True, align="c")
        P.text("LÄUFT GERADE", 15, 187, 182, T["muted"], bold=True)
        self.marquee = False
        if self.game:
            g = self.game
            # Langer Titel: Laufschrift von rechts nach links
            x0, x1 = 187, 935
            tw = P.width(g["name"], 28, bold=True, raw=True)
            if tw <= x1 - x0:
                P.text(g["name"], 28, x0, 222, T["text"], bold=True, raw=True)
            else:
                self.marquee = True
                gap = 90
                t = time.monotonic() - self.marquee_t0
                off = 0 if t < 1.5 else ((t - 1.5) * 70) % (tw + gap)
                P.clip(x0, 185, x1 - x0, 50)
                P.text(g["name"], 28, x0 - off, 222, T["text"], bold=True, raw=True)
                P.text(g["name"], 28, x0 - off + tw + gap, 222, T["text"], bold=True, raw=True)
                P.unclip()
            sub = " · ".join(p for p in (g["system"], g["emu"]) if p)
            if g["played"] is not None:
                mins = int(g["played"] // 60)
                sub += f" · {mins // 60}:{mins % 60:02d} h"
            P.text(sub, 18, 187, 253, T["muted"])
            gfocus = self.rows()[self.focus][0] == "game"
            P.rrect(955, 181, 233, 63, 32, A, a=1.0 if gfocus else 0.45)
            P.text("Spiel beenden", 21, 1071, 220, "ffffff", bold=True, align="c")
            if gfocus:
                self._focus_ring(P, 955, 181, 233, 63, 32)
            self.hits.append((955, 175, 233, 75, ("quit", None)))
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
            P.rrect(x0, cy - 6, x1 - x0, 12, 6, mix(T["track"], A, 0.35))
            P.rrect(x0, cy - 6, max(12, (x1 - x0) * val / 100), 12, 6, A)
            P.circle(x0 + (x1 - x0) * val / 100, cy, 13, mix(A, "ffffff", 0.45))
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
            P.rrect(sx, y + 14, 269, 61, 16, A if active else mix(T["seg"], A, 0.12))
            P.text(name, 20, sx + 134, y + 52, "ffffff" if active else T["text"],
                   bold=active, align="c")
            if focused and i == self.perf_sel:
                self._focus_ring(P, sx, y + 14, 269, 61, 16)
            self.hits.append((sx, y + 10, 269, 70, ("perf", i)))
        y += 110

        states = [bool(self.wifi[0]), bool(self.bt[0]), False, False, False]  # Screen-aus = inaktiv (nicht eingefärbt)
        focused = rows[self.focus][0] == "tiles"
        # Kacheln – eine Reihe, gleiche Breite
        n = len(TILES)
        gap = 15
        tw = (1170 - (n - 1) * gap) // n
        th = 118
        ry = y
        for i, name in enumerate(TILES):
            tx = 45 + i * (tw + gap)
            fill = A if states[i] else mix(T["tile"], A, 0.22)
            P.rrect(tx, ry, tw, th, 24, fill)
            tc = "ffffff" if states[i] else T["text"]
            sub = self._tile_detail(i)
            P.text(name, 21, tx + 25, ry + (68 if sub else 79), tc, bold=True)
            if sub:
                P.text(sub, 16, tx + 25, ry + 96, mix(tc, fill, 0.25))
            if i < 2:   # WLAN/BT Untermenü-Pfeil
                P.circle(tx + tw - 38, ry + 38, 22, mix(fill, "ffffff" if states[i] else T["text"], 0.18))
                P.chevron(tx + tw - 34, ry + 38, 9, "ffffff" if states[i] else T["text"])
                self.hits.append((tx + tw - 82, ry, 82, 80, ("more", i)))
            if focused and i == self.tile:
                self._focus_ring(P, tx, ry, tw, th, 24)
            self.hits.append((tx, ry, tw, th, ("tile", i)))

    def _tile_detail(self, i):
        """Zweite Zeile der WLAN-/Bluetooth-Kachel."""
        def short(t, n=20):
            return t if len(t) <= n else t[:n - 1] + "…"
        if i == 0:
            on, ssid = self.wifi
            return short(ssid) if ssid else ("Nicht verbunden" if on else "Aus")
        if i == 1:
            on, names = self.bt
            if not on:
                return "Aus"
            if not names:
                return "Kein Gerät"
            return short(names[0], 16 if len(names) > 1 else 20) + (f" +{len(names) - 1}" if len(names) > 1 else "")
        return ""

    def _draw_placeholder(self, P):
        T = self.T
        P.text(PAGES[self.page], 44, 630, 420, T["text"], bold=True, align="c")
        stage = "Etappe 2" if self.page == 1 else "Etappe 3"
        P.text(f"kommt in {stage}", 22, 630, 470, T["muted"], align="c")

    def _draw_loading(self, P):
        """Unterer Bildschirm während des Wechsels."""
        T, A = self.T, self.accent
        it, fresh = self.loading or ({"name": ""}, False)
        P.logo(630 - 115 * 0.8, 330, 130 * 0.8, T["text"], T["bg"])
        P.text("Wird neu gestartet …" if fresh else "Wird fortgesetzt …", 30, 630, 520, T["muted"], align="c")
        name = it.get("name", "")
        while P.width(name, 40, bold=True, raw=True) > 1150 and len(name) > 4:
            name = name[:-2]
        P.text(name if name == it.get("name") else name.rstrip() + "…", 40, 630, 580,
               T["text"], bold=True, align="c", raw=True)
        # einfache Fortschrittsanzeige (läuft, solange gezeichnet wird)
        t = time.monotonic() * 2.2
        for k in range(3):
            a = 0.3 + 0.7 * max(0.0, math.sin(t - k * 0.7))
            P.rrect(630 - 50 + k * 40 - 8, 640, 16, 16, 8, A, a=a)

    def paint_top_loading(self, cr, w, h):
        """Oberer Bildschirm während des Wechsels: Spiel-Icon groß, Name, Hinweis."""
        T, A = self.T, self.accent
        P = Pen(cr, w, h)
        P.fill_all(T["bg"])
        it, fresh = self.loading or ({}, False)
        icon = it.get("icon")
        size = 380
        x, y = 630 - size / 2, 150
        if not (icon and os.path.exists(icon) and P.image(icon, x, y, size, size, 48)):
            P.rrect(x, y, size, size, 48, T["tile"])
            P.text((it.get("name") or "?")[:1].upper(), 200, 630, y + size / 2 + 72, T["muted"],
                   bold=True, align="c", raw=True)
        name = it.get("name", "")
        while P.width(name, 46, bold=True, raw=True) > 1150 and len(name) > 4:
            name = name[:-2]
        P.text(name if name == it.get("name") else name.rstrip() + "…", 46, 630, 640,
               T["text"], bold=True, align="c", raw=True)
        P.text("Wird neu gestartet …" if fresh else "Wird fortgesetzt …", 28, 630, 700, T["muted"], align="c")
        sub = " · ".join(p for p in (it.get("system"), it.get("emu")) if p)
        if sub:
            P.text(sub, 22, 630, 745, T["muted"], align="c", raw=True)

    def _draw_switcher(self, P):
        T, A = self.T, self.accent
        sw = self.switcher
        now = time.localtime()
        P.text(time.strftime("%H:%M", now), 52, 45, 90, T["text"], bold=True)
        lw = 230 * 52 / 130
        tw = P.width("Gameswitcher", 38, bold=True)
        lx = (1260 - lw - 16 - tw) / 2
        P.logo(lx, 97 - 26, 52, T["text"], T["bg"])
        P.text("Gameswitcher", 38, lx + lw + 16, 97 + 38 * 0.36, T["text"], bold=True)
        if sw.busy:
            P.text(sw.busy, 30, 630, 480, T["text"], bold=True, align="c", raw=True)
            return
        if not sw.items:
            P.text("Noch keine Spiele gespielt", 30, 630, 460, T["text"], bold=True, align="c")
            P.text("Home oder B: schließen", 18, 630, 925, T["muted"], align="c")
            return
        # Karussell: ausgewählte Karte groß in der Mitte, Nachbarn links/rechts
        cw, ch = 560, 420
        cy = 170
        for k in (-2, -1, 1, 2, 0):           # Mitte zuletzt (oben drauf)
            i = sw.sel + k
            if not 0 <= i < len(sw.items):
                continue
            it = sw.items[i]
            sc = 1.0 if k == 0 else 0.6
            w, h = cw * sc, ch * sc
            x = 630 + k * 430 - w / 2
            y = cy + (ch - h) / 2
            P.rrect(x, y, w, h, 26, T["card"])
            shot = it.get("shot")
            if not (shot and os.path.exists(shot) and P.image(shot, x, y, w, h, 26)):
                icon = it.get("icon")
                if not (icon and P.image(icon, x + w / 2 - 70 * sc, y + h / 2 - 70 * sc, 140 * sc, 140 * sc, 20)):
                    P.text(it["name"][:1].upper(), 90 * sc, x + w / 2, y + h / 2 + 30 * sc, T["muted"], bold=True, align="c", raw=True)
            if k == 0:
                P.rrect(x - 6, y - 6, w + 12, h + 12, 32, A, stroke=5)
            else:
                P.rrect(x, y, w, h, 26, T["bg"], a=0.45)
            self.hits.append((x, y, w, h, ("gs", i)))
        it = sw.items[sw.sel]
        name = it["name"]
        while P.width(name, 32, bold=True, raw=True) > 1100 and len(name) > 4:
            name = name[:-2]
        if name != it["name"]:
            name = name.rstrip() + "…"
        P.text(name, 32, 630, 660, T["text"], bold=True, align="c", raw=True)
        mins = int((time.time() - it.get("time", time.time())) // 60)
        ago = ("gerade eben" if mins < 1 else f"vor {mins} min" if mins < 60
               else f"vor {mins // 60} h" if mins < 1440 else f"vor {mins // 1440} Tagen")
        sub = " · ".join(p for p in (it.get("system"), it.get("emu"), tr(ago)) if p)
        P.text(sub, 20, 630, 700, T["muted"], align="c", raw=True)
        # Seitenpunkte
        n = len(sw.items)
        for i in range(n):
            P.circle(630 + (i - (n - 1) / 2) * 22, 745, 6 if i == sw.sel else 4, A if i == sw.sel else T["dot"])
        # Tasten
        btns = [("A", "Weiterspielen"), ("Y", "Neu starten"), ("X", "Optionen (bald)"), ("B", "Schließen")]
        bx = 630 - 4 * 270 / 2
        for j, (key, label) in enumerate(btns):
            x = bx + j * 270
            P.rrect(x + 10, 790, 250, 70, 35, A if j == 0 else T["card"], a=1.0 if j != 2 else 0.5)
            P.text(f"{key}  {tr(label)}", 20, x + 135, 832, "ffffff" if j == 0 else T["text"], bold=j == 0, align="c", raw=True)
            self.hits.append((x + 10, 790, 250, 70, ("gs_btn", key)))
        if it.get("emu") in ("PortMaster",):
            P.text("Spielstand über das Spiel selbst", 17, 630, 905, T["muted"], align="c")


# ------------------------------------------------------------ Power-Menü ----

POWER_ITEMS = [
    ("power_sleep",   "Ruhemodus",      "systemctl suspend",  False),
    ("power_restart", "Neu starten",    "systemctl reboot",   True),   # True = hat Untermenü
    ("power_off",     "Ausschalten",    "systemctl poweroff", False),
    ("power_es",      "ES neu starten", None,                 False),  # Sonderfall: Rückfrage
]

LOG_DIR = "/storage/logs"
LOG_SOURCES = [
    "/var/log/rds-controlcenter.log",
    "/var/log/messages",
    "/storage/.config/emulationstation/es_log.txt",
    "/tmp/retroarch.log",
]

def save_logs():
    """Logs in ein tar.gz-Archiv packen. Gibt den Pfad zurück oder None bei Fehler."""
    import tarfile, datetime
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = f"{LOG_DIR}/rds-report-{ts}.tar.gz"
    try:
        with tarfile.open(out, "w:gz") as tar:
            for src in LOG_SOURCES:
                if os.path.exists(src):
                    tar.add(src, arcname=os.path.basename(src))
        log("Logs gesichert:", out)
        return out
    except Exception as exc:
        log("Log-Sicherung fehlgeschlagen:", exc)
        return None


class PowerMenu:
    """Power-Menü – Hauptliste + Neustart-Untermenü mit Log-Option."""

    # Zustände
    STATE_MAIN    = "main"
    STATE_RESTART = "restart"   # Neustart-Untermenü
    STATE_ES      = "es"        # Rückfrage ES-Neustart

    def __init__(self, cc):
        self.cc = cc
        self.focus = 0
        self.sub_focus = 0        # Fokus im Neustart-Untermenü
        self.confirm_es_focus = 0 # 0 = Ja, 1 = Nein (ES-Rückfrage)
        self.state = self.STATE_MAIN

    # -- Untermenü-Einträge für Neu starten --
    RESTART_ITEMS = [
        ("Neu starten",              "systemctl reboot"),
        ("Neu starten + Logs sichern", None),   # Sonderfall: erst Logs, dann reboot
    ]

    def nav(self, dx, dy):
        if self.state == self.STATE_MAIN:
            self.focus = (self.focus + dy) % len(POWER_ITEMS)
        elif self.state == self.STATE_RESTART:
            self.sub_focus = (self.sub_focus + dy) % len(self.RESTART_ITEMS)
        elif self.state == self.STATE_ES:
            # links/rechts zwischen Ja und Nein (confirm_es_focus: 0=Ja, 1=Nein)
            if dx:
                self.confirm_es_focus = (self.confirm_es_focus + dx) % 2

    def confirm(self):
        """A gedrückt. Gibt False zurück wenn das Menü geschlossen werden soll."""
        if self.state == self.STATE_MAIN:
            key, _label, cmd, has_sub = POWER_ITEMS[self.focus]
            if key == "power_es":
                self.state = self.STATE_ES
                return True
            self._run(cmd)
            return False
        elif self.state == self.STATE_RESTART:
            label, cmd = self.RESTART_ITEMS[self.sub_focus]
            if cmd is None:
                save_logs()
                self._run("systemctl reboot")
            else:
                self._run(cmd)
            return False
        elif self.state == self.STATE_ES:
            if self.confirm_es_focus == 0:
                self._run("systemctl restart essway")
                return False
            else:
                self.state = self.STATE_MAIN   # Abbrechen
                return True
        return False

    def details(self):
        """X gedrückt oder Pfeil-Touch auf Neu starten → Untermenü öffnen."""
        if self.state == self.STATE_MAIN:
            _key, _label, _cmd, has_sub = POWER_ITEMS[self.focus]
            if has_sub:
                self.state = self.STATE_RESTART
                self.sub_focus = 0
                return True
        return False

    def cancel(self):
        """B gedrückt. Gibt False zurück wenn das Menü geschlossen werden soll."""
        if self.state in (self.STATE_RESTART, self.STATE_ES):
            self.state = self.STATE_MAIN
            self.confirm_es_focus = 0
            return True
        return False

    def _run(self, cmd):
        log("Power-Aktion:", cmd)
        def _go():
            time.sleep(0.3)   # Overlay hat Zeit sich zu schließen
            subprocess.Popen(["bash", "-c", cmd])
        threading.Thread(target=_go, daemon=True).start()

    def touch_up(self, x, y, hits):
        """hits: Liste von (hx, hy, hw, hh, action) mit action = ('item',i) | ('more',i) | ('yes'|'no')."""
        for hx, hy, hw, hh, action in hits:
            if hx <= x <= hx + hw and hy <= y <= hy + hh:
                if isinstance(action, tuple):
                    kind, idx = action
                    if kind == "item":
                        if self.state == self.STATE_MAIN:
                            self.focus = idx
                            return self.confirm()
                        elif self.state == self.STATE_RESTART:
                            self.sub_focus = idx
                            return self.confirm()
                    elif kind == "more":
                        self.focus = idx
                        self.details()
                        return True
                elif action == "yes":
                    return self.confirm()
                elif action == "no":
                    self.cancel()
                    return True
        return None   # kein Treffer → kein close-Signal

    def draw(self, P, T, accent):
        hits = []
        W, H = 1260, 951
        bx = 60
        bw = W - 120
        bh = 110

        P.fill_all(T["bg"])

        # Titel mit Logo
        lh = 52
        lw = 230 * lh / 130
        lx = (W - lw - 16 - P.width("Power", 38, bold=True)) / 2
        P.logo(lx, 72 - lh / 2, lh, T["text"], T["bg"])
        P.text("Power", 38, lx + lw + 16, 72 + 38 * 0.36, T["text"], bold=True)
        P.rrect(60, 116, W - 120, 2, 1, T["dot"])

        if self.state == self.STATE_ES:
            # Rückfrage ES-Neustart
            P.text("ES wirklich neu starten?", 30, W / 2, H / 2 - 60, T["text"], bold=True, align="c")
            P.text("Laufendes Spiel geht verloren.", 22, W / 2, H / 2 - 18, T["muted"], align="c")
            cbw = (bw - 30) / 2
            for i, label in enumerate(["Ja, neu starten", "Abbrechen"]):
                bxi = bx + i * (cbw + 30)
                byi = H / 2 + 40
                active = i == self.confirm_es_focus
                if active:
                    P.rrect(bxi, byi, cbw, 90, 20, accent)
                else:
                    P.rrect(bxi, byi, cbw, 90, 20, T["bg"])
                    P.rrect(bxi, byi, cbw, 90, 20, T["dot"], stroke=2)
                P.text(label, 24, bxi + cbw / 2, byi + 52,
                       "ffffff" if active else T["muted"], bold=active, align="c")
                hits.append((bxi, byi, cbw, 90, "yes" if i == 0 else "no"))
            P.text("◄ ► Auswahl  ·  A Bestätigen  ·  B Abbrechen", 17, W / 2, H - 36, T["muted"], align="c")

        elif self.state == self.STATE_RESTART:
            # Neustart-Untermenü
            P.text("Neu starten", 26, W / 2, 160, T["muted"], align="c")
            n = len(self.RESTART_ITEMS)
            total_h = n * bh + (n - 1) * 20
            by0 = (H - total_h) / 2 + 30
            for i, (label, _cmd) in enumerate(self.RESTART_ITEMS):
                by = by0 + i * (bh + 20)
                active = i == self.sub_focus
                if active:
                    P.rrect(bx, by, bw, bh, 24, accent)
                else:
                    P.rrect(bx, by, bw, bh, 24, T["bg"])
                    P.rrect(bx, by, bw, bh, 24, T["dot"], stroke=2)
                P.text(label, 28, bx + bw / 2, by + bh / 2 + 28 * 0.36,
                       "ffffff" if active else T["muted"], bold=active, align="c")
                hits.append((bx, by, bw, bh, ("item", i)))
            P.text("B Zurück", 19, W / 2, H - 36, T["muted"], align="c")

        else:
            # Hauptliste
            n = len(POWER_ITEMS)
            total_h = n * bh + (n - 1) * 20
            by0 = (H - total_h) / 2 + 30
            for i, (_key, label, _cmd, has_sub) in enumerate(POWER_ITEMS):
                by = by0 + i * (bh + 20)
                active = i == self.focus
                if active:
                    P.rrect(bx, by, bw, bh, 24, accent)
                else:
                    P.rrect(bx, by, bw, bh, 24, T["bg"])
                    P.rrect(bx, by, bw, bh, 24, T["dot"], stroke=2)
                P.text(label, 28, bx + bw / 2, by + bh / 2 + 28 * 0.36,
                       "ffffff" if active else T["muted"], bold=active, align="c")
                hits.append((bx, by, bw, bh, ("item", i)))
                if has_sub:
                    # Pfeil rechts innen im Button
                    tc = "ffffff" if active else T["muted"]
                    circ_fill = mix(accent, "000000", 0.18) if active else T["dot"]
                    P.circle(bx + bw - 52, by + bh / 2, 22, circ_fill)
                    P.chevron(bx + bw - 48, by + bh / 2, 9, tc)
                    hits.append((bx + bw - 90, by, 90, bh, ("more", i)))
            P.text("B Abbrechen  ·  X Details", 19, W / 2, H - 36, T["muted"], align="c")

        return hits


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
        self.output_ids = {}  # Registry-Name -> proxy (für global_remove)
        self.surface = self.lsurf = self.buffer = None
        self.view = None
        self.size = None
        self.touch_id = None
        self.pending_view = None
        self._mm = None
        self.top = None   # Fläche auf dem oberen Bildschirm (Ladebildschirm)

        self.registry = marshal(self.display, 1, IF_REGISTRY, ("n", None))
        G = CFUNCTYPE(None, c_void_p, c_void_p, c_uint32, c_char_p, c_uint32)
        R = CFUNCTYPE(None, c_void_p, c_void_p, c_uint32)
        listen(self.registry, G(self._on_global), R(self._on_global_remove))
        wl.wl_display_roundtrip(self.display)
        wl.wl_display_roundtrip(self.display)
        if not (self.compositor and self.shm and self.layer_shell):
            sys.exit("Compositor bietet keine Layer-Shell an")
        log("Bildschirme:", ", ".join(self.outputs.values()) or "?",
            "| verwende", OUTPUT_NAME if self.current_output() else "Standard")
    
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
            self.output_ids[name] = out
            if self.compositor:   # nachträglich (wieder) erschienen, z. B. nach dem Einschalten
                log("Bildschirm angemeldet (Registry %d)" % name)
            self._listen_output(out)
        elif iface == b"wl_seat" and not self.seat:
            self.seat = self._bind(name, IF_SEAT, min(version, 5))
            listen(self.seat,
                   CFUNCTYPE(None, c_void_p, c_void_p, c_uint32)(self._on_caps),
                   CFUNCTYPE(None, c_void_p, c_void_p, c_char_p)(lambda *a: None))

    @safe
    def _on_global_remove(self, _data, _reg, name):
        out = self.output_ids.pop(name, None)
        if out is not None:
            log("Bildschirm abgemeldet:", self.outputs.pop(out, "?"))
            if self.surface and self.view:
                view = self.view          # liegt auf dem verschwundenen Bildschirm → neu anlegen
                self.hide(quiet=True)
                self.pending_view = view

    def current_output(self):
        """Den unteren Bildschirm bei jedem Öffnen frisch suchen (er kann neu angemeldet worden sein)."""
        return next((o for o, n in reversed(list(self.outputs.items())) if n == OUTPUT_NAME), None)

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
                             ("o", self.surface), ("o", self.current_output()),
                             ("u", LAYER_OVERLAY), ("s", b"rds-controlcenter"))
        listen(self.lsurf,
               CFUNCTYPE(None, c_void_p, c_void_p, c_uint32, c_uint32, c_uint32)(self._on_configure),
               CFUNCTYPE(None, c_void_p, c_void_p)(self._on_closed))
        marshal(self.lsurf, 1, None, ("u", ANCHOR_ALL))     # set_anchor
        marshal(self.lsurf, 2, None, ("i", -1))             # set_exclusive_zone
        marshal(self.surface, 6, None)                      # commit
        wl.wl_display_flush(self.display)
        log("angezeigt:", view, "auf", self.outputs.get(self.current_output(), "Standard"))

    @safe
    def _on_closed(self, _d, _lsurf):
        log("Compositor hat die Fläche geschlossen – lege sie neu an")
        view = self.view
        self.hide(quiet=True)
        if view != "power":   # Power-Menü nie automatisch wiederherstellen
            self.pending_view = view

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

    # -- oberer Bildschirm (nur Anzeige, z. B. Ladebildschirm des Gameswitchers) --
    def top_output(self):
        return next((o for o, n in reversed(list(self.outputs.items())) if n == TOP_OUTPUT), None)

    def show_top(self, painter):
        self.hide_top()
        out = self.top_output()
        if not out:
            return
        t = {"painter": painter, "size": None, "buffer": None, "mm": None}
        t["surface"] = marshal(self.compositor, 0, IF_SURFACE, ("n", None))
        t["lsurf"] = marshal(self.layer_shell, 0, IF_LAYER_SURFACE, ("n", None),
                             ("o", t["surface"]), ("o", out),
                             ("u", LAYER_OVERLAY), ("s", b"rds-top"))

        def configure(_d, lsurf, serial, w, h):
            try:
                marshal(lsurf, 6, None, ("u", serial))
                t["size"] = (w or 1024, h or 768)
                self.redraw_top()
            except Exception as exc:
                log("Fehler oben:", exc)
        listen(t["lsurf"],
               CFUNCTYPE(None, c_void_p, c_void_p, c_uint32, c_uint32, c_uint32)(configure),
               CFUNCTYPE(None, c_void_p, c_void_p)(lambda *a: None))
        marshal(t["lsurf"], 1, None, ("u", ANCHOR_ALL))
        marshal(t["lsurf"], 2, None, ("i", -1))
        marshal(t["surface"], 6, None)
        wl.wl_display_flush(self.display)
        self.top = t

    def redraw_top(self):
        t = self.top
        if not (t and t["size"]):
            return
        w, h = t["size"]
        stride = w * 4
        size = stride * h
        fd = os.memfd_create("rds-top", 0)
        os.ftruncate(fd, size)
        mm = mmap.mmap(fd, size)
        ptr = ctypes.addressof(c_char.from_buffer(mm))
        surf = cairo.cairo_image_surface_create_for_data(ptr, 0, w, h, stride)
        cr = cairo.cairo_create(surf)
        try:
            t["painter"](cr, w, h)
        finally:
            cairo.cairo_surface_flush(surf)
            cairo.cairo_destroy(cr)
            cairo.cairo_surface_destroy(surf)
        pool = marshal(self.shm, 0, IF_SHM_POOL, ("n", None), ("h", fd), ("i", size))
        old = t["buffer"]
        t["buffer"] = marshal(pool, 0, IF_BUFFER, ("n", None), ("i", 0), ("i", w),
                              ("i", h), ("i", stride), ("u", 0))
        marshal(pool, 1, None, destroy=True)
        os.close(fd)
        marshal(t["surface"], 1, None, ("o", t["buffer"]), ("i", 0), ("i", 0))
        marshal(t["surface"], 9, None, ("i", 0), ("i", 0), ("i", w), ("i", h))
        marshal(t["surface"], 6, None)
        if old:
            marshal(old, 0, None, destroy=True)
        t["mm"] = mm
        wl.wl_display_flush(self.display)

    def hide_top(self):
        t, self.top = self.top, None
        if not t:
            return
        marshal(t["lsurf"], 7, None, destroy=True)
        marshal(t["surface"], 0, None, destroy=True)
        if t["buffer"]:
            marshal(t["buffer"], 0, None, destroy=True)
        wl.wl_display_flush(self.display)

    # -- Ereignisschleife --
    def _check(self, result):
        """Bricht ab, wenn die Verbindung zum Compositor weg ist (z. B. Sway neu gestartet).
        Der Dienst startet das Kontrollcenter dann neu und verbindet sich frisch."""
        if result < 0 or wl.wl_display_get_error(self.display):
            raise ConnectionError("Verbindung zu Sway verloren")
        return result

    def pump(self, timeout, extra_fds):
        d = self.display
        while wl.wl_display_prepare_read(d) != 0:
            self._check(wl.wl_display_dispatch_pending(d))
        wl.wl_display_flush(d)
        wfd = wl.wl_display_get_fd(d)
        ready, _, _ = select.select([wfd] + extra_fds, [], [], timeout)
        if wfd in ready:
            self._check(wl.wl_display_read_events(d))
        else:
            wl.wl_display_cancel_read(d)
        self._check(wl.wl_display_dispatch_pending(d))
        return [fd for fd in ready if fd != wfd]


# ----------------------------------------------------------------- Tasten ----

EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
ABS_X, ABS_Y, ABS_RX, ABS_RY, ABS_HAT0X, ABS_HAT0Y = 0, 1, 3, 4, 16, 17
BTN_SELECT, BTN_START = 314, 315
BTN_TOUCH = 330
BTN_SOUTH, BTN_EAST, BTN_TL, BTN_TR, BTN_MODE, BTN_Z = 304, 305, 310, 311, 316, 309
DPAD = {544: (0, -1), 545: (0, 1), 546: (-1, 0), 547: (1, 0)}   # BTN_DPAD_*
BTN_NORTH, BTN_WEST = 307, 308
KNOWN_UNUSED = {312, 313, 314, 315}   # X, Y, L2, R2, Select, Start
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


def list_gamepads():
    """Pfad -> Name aller Gamepads (Geräte mit js-Handler) laut /proc/bus/input/devices."""
    res, name = {}, None
    try:
        with open("/proc/bus/input/devices") as f:
            for line in f:
                if line.startswith("N: Name="):
                    name = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("H: Handlers="):
                    parts = line.split("=", 1)[1].split()
                    ev = next((p for p in parts if p.startswith("event")), None)
                    if ev and any(p.startswith("js") for p in parts):
                        res["/dev/input/" + ev] = name
    except OSError:
        pass
    return res


def open_event(name):
    path = find_event(name)
    if not path:
        log("Eingabegerät nicht gefunden:", name)
        return None
    log("Eingabegerät", name, "->", path)
    return os.open(path, os.O_RDONLY | os.O_NONBLOCK)


def read_events(fd, types=(EV_KEY, EV_ABS)):
    try:
        data = os.read(fd, EVENT.size * 64)
    except BlockingIOError:
        return []
    out = []
    for off in range(0, len(data) - EVENT.size + 1, EVENT.size):
        _s, _us, typ, code, value = EVENT.unpack_from(data, off)
        if typ in types:
            out.append((typ, code, value))
    return out


def abs_range(fd, code):
    buf = bytearray(24)  # struct input_absinfo
    try:
        fcntl.ioctl(fd, 0x80184540 + code, buf)  # EVIOCGABS(code)
    except OSError:
        return 0, 1
    _val, lo, hi = struct.unpack_from("iii", buf)
    return lo, (hi if hi > lo else lo + 1)


class TouchReader:
    """Liest den Touchscreen direkt (Einzelfinger-Emulation: ABS_X/ABS_Y + BTN_TOUCH)."""

    def __init__(self, fd, cfg):
        self.rx, self.ry = abs_range(fd, ABS_X), abs_range(fd, ABS_Y)
        self.cfg = cfg
        self.x = self.y = 0
        self.down = False
        self.change = None
        log("Touch-Bereich roh: x", self.rx, "y", self.ry)

    def feed(self, typ, code, value):
        """Liefert ('down'|'move'|'up', nx, ny) mit nx/ny 0..1 (Rohachsen) oder None."""
        if typ == EV_ABS and code == ABS_X:
            self.x = value
            self.change = self.change or ("move" if self.down else None)
        elif typ == EV_ABS and code == ABS_Y:
            self.y = value
            self.change = self.change or ("move" if self.down else None)
        elif typ == EV_KEY and code == BTN_TOUCH:
            self.down = value == 1
            self.change = "down" if self.down else "up"
        elif typ == EV_SYN and self.change:
            kind, self.change = self.change, None
            nx = (self.x - self.rx[0]) / (self.rx[1] - self.rx[0])
            ny = (self.y - self.ry[0]) / (self.ry[1] - self.ry[0])
            return kind, nx, ny
        return None

    def to_surface(self, nx, ny, w, h):
        raw_landscape = (self.rx[1] - self.rx[0]) >= (self.ry[1] - self.ry[0])
        swap = self.cfg.get("touch_swap", raw_landscape != (w >= h))
        if swap:
            nx, ny = ny, nx
        if self.cfg.get("touch_flip_x"):
            nx = 1 - nx
        if self.cfg.get("touch_flip_y"):
            ny = 1 - ny
        return nx * w, ny * h


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
        if ui.view == "loading":
            return
        if ui.view == "switcher":
            if kind == "up" and cc.pen:
                dx, dy = cc.pen.to_design(x, y)
                hit = next((h[4] for h in reversed(cc.hits)
                            if h[0] <= dx <= h[0] + h[2] and h[1] <= dy <= h[1] + h[3]), None)
                if hit and hit[0] == "gs":
                    if hit[1] == cc.switcher.sel:
                        gs_act(False)
                    else:
                        cc.switcher.sel = hit[1]
                elif hit and hit[0] == "gs_btn":
                    {"A": lambda: gs_act(False), "Y": lambda: gs_act(True),
                     "B": lambda: toggle("switcher")}.get(hit[1], lambda: None)()
                state["dirty"] = True
            return
        if ui.view == "power":
            if kind == "up" and cc.pen:
                dx, dy = cc.pen.to_design(x, y)
                result = cc.power_menu.touch_up(dx, dy, cc.power_hits)
                if result is False:
                    toggle("power")
                state["dirty"] = True
            return
        if ui.view != "cc":
            return
        result = {"down": cc.touch_down, "move": cc.touch_move}.get(kind, lambda *_: cc.touch_up())(x, y)
        if result == "power":
            toggle("power")
        elif result == "close":
            toggle("cc")
        elif result == "quit":
            do_quit()
        state["dirty"] = True

    ui = Overlay(cc.draw, on_touch)
    joy = open_event(JOYPAD_NAME)
    pads = {}   # fd -> {"name", "path", "ext", "range"}: eingebautes Joypad + externe Controller
    if joy is not None:
        pads[joy] = {"name": JOYPAD_NAME, "path": find_event(JOYPAD_NAME), "ext": False,
                     "range": abs_range(joy, ABS_X)}
    home = open_event(HOME_NAME)
    pwr = open_event(POWER_NAME)
    pwr_down_at = None   # Zeitstempel des Drückens (für Kurz/Lang)
    tfd = open_event(TOUCH_NAME)
    touch = TouchReader(tfd, cc.cfg) if tfd is not None else None
    mode_down = combo = False
    grabbed = False

    def set_grab(on):
        # alle Controller und der Touchscreen gehören nur uns, solange das Overlay offen ist
        nonlocal grabbed
        if grabbed != on:
            for fd in list(pads) + [tfd]:
                if fd is not None:
                    grab(fd, on)
            grabbed = on

    def scan_pads():
        """Externe Controller erkennen (auch später verbundene) bzw. entfernen."""
        known = {v["path"]: fd for fd, v in pads.items()}
        found = list_gamepads()
        for path, name in found.items():
            if path in known:
                continue
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            except OSError:
                continue
            pads[fd] = {"name": name, "path": path, "ext": True, "range": abs_range(fd, ABS_X)}
            log("Controller verbunden:", name, "->", path)
            if grabbed:
                grab(fd, True)
        for path, fd in known.items():
            if path not in found and pads[fd]["ext"]:
                drop_pad(fd)

    def drop_pad(fd):
        info = pads.pop(fd, None)
        if info:
            log("Controller getrennt:", info["name"])
        try:
            os.close(fd)
        except OSError:
            pass

    pauser = Pauser()

    def toggle(view):
        if ui.pending_view and not ui.view:
            ui.view, ui.pending_view = ui.pending_view, None   # zählt noch als offen
        if ui.view == view:
            if getattr(cc, "redim", False) and cc.game and cc.game["emu"] in AUTO_DIM_EMUS:
                cc.screen_off()   # RetroArch: beim Schließen wieder abdunkeln
                cc.screen_auto = True
            cc.redim = False
            cc.reset()
            cc.power_menu.state = cc.power_menu.STATE_MAIN   # Zustand zurücksetzen
            ui.hide()
            set_grab(False)
            pauser.resume()
        else:
            if not ui.view:
                if cc.screen_bottom_off and cc.screen_auto:   # automatisch abgedunkelt → für die Anzeige an
                    cc.screen_on()
                    cc.redim = True
                cc.refresh(full=True)
                if view == "switcher":
                    sw = cc.switcher
                    sw.load()
                    sw.sel = 0
                    if cc.game:
                        # sofort anzeigen, speichern im Hintergrund; Pause + Grab erst danach
                        # (eingespeiste Tasten erreichen den Emulator nur ohne Grab)
                        sw.busy = tr("Spiel wird gespeichert …")
                        ui.show(view)
                        state["dirty"] = True
                        game = cc.game
                        def work():
                            try:
                                sw.capture(game)
                            except Exception:
                                log("Gameswitcher: Speichern fehlgeschlagen:\n" + traceback.format_exc().rstrip())
                            sw.ready = True
                        threading.Thread(target=work, daemon=True).start()
                        return
                pauser.pause(cc.game)
            ui.show(view)          # wechselt auch direkt zwischen den Ansichten
            set_grab(True)

    def gs_act(fresh):
        """A (fresh=False) weiterspielen, Y (fresh=True) neu starten."""
        sw = cc.switcher
        if not sw.items:
            return
        item = sw.items[sw.sel]
        cur = cc.game
        same = cur and (cur.get("rom") or rom_of(cur["pid"])) == item["rom"]
        if same and fresh and cur["emu"] == "RetroArch":
            ra_command("RESET")             # im laufenden RetroArch neu starten, ohne Beenden
            time.sleep(0.3)
            toggle("switcher")              # danach Pause aufheben
            def unpause():                  # Sicherheitsnetz: RetroArch nie pausiert zurücklassen
                time.sleep(0.8)
                st = ra_command("GET_STATUS", reply=True) or ""
                if "PAUSED" in st:
                    ra_command("PAUSE_TOGGLE")
            threading.Thread(target=unpause, daemon=True).start()
            log("Gameswitcher: RetroArch zurückgesetzt", item["name"])
            return
        toggle("switcher")                 # schließen, Pause aufheben
        if same and not fresh:
            return                          # einfach zurück ins laufende Spiel
        # Ladebildschirm auf beiden Screens, bis das Spiel läuft und der Stand geladen ist
        cc.loading = (item, fresh)
        cc.loading_t0 = time.monotonic()
        if cc.screen_bottom_off:
            cc.screen_on()
        ui.show("loading")
        ui.show_top(cc.paint_top_loading)
        sw.launch(item, fresh, current=cur)

    stick = {"dir": 0, "next": 0.0}

    def handle_stick(value, rng):
        """Linker Stick links/rechts: Cursor in der Tastatur bewegen (mit Wiederholung)."""
        lx_lo, lx_hi = rng
        n = (value - (lx_lo + lx_hi) / 2) / ((lx_hi - lx_lo) / 2)
        d = 1 if n > 0.6 else -1 if n < -0.6 else 0
        if d != stick["dir"]:
            stick["dir"] = d
            if d and ui.view and cc.kbd:
                cc.kbd.cursor(d)
                stick["next"] = time.monotonic() + 0.4
                state["dirty"] = True

    def do_quit():
        game = cc.game
        if ui.view:
            toggle(ui.view)   # schließt CC und hebt die Pause auf
        quit_game(game)
        cc.game = None

    def handle_joy(typ, code, value, pad):
        nonlocal mode_down, combo
        if pad["ext"] and typ == EV_KEY and code in (BTN_SOUTH, BTN_EAST):
            # externe Controller nach Xbox-Art: A (unten) bestätigt, B (rechts) zurück
            code = BTN_EAST if code == BTN_SOUTH else BTN_SOUTH
        if typ == EV_ABS and code not in (ABS_HAT0X, ABS_HAT0Y):
            if code == ABS_X:
                handle_stick(value, pad["range"])
            return   # Sticks/Trigger nie als Tastendruck werten (Drift stört sonst die Home-Taste)   # Sticks nie als Tastendruck werten (sonst stört Stick-Drift die Anbernic-Taste)
        if typ == EV_KEY and code == BTN_MODE:
            if value == 1:
                mode_down, combo = True, False
            elif value == 0:
                if mode_down and not combo:
                    toggle("cc")
                mode_down = False
            return
        if typ == EV_KEY and code == BTN_EAST and cc.kbd and ui.view and not mode_down:
            if value == 1:
                cc.kbd.a_down()
            elif value == 0:
                cc.kbd.a_up()
                state["dirty"] = True
            return
        pressed = value != 0 if typ == EV_ABS else value == 1
        if not pressed:
            return
        if mode_down:
            combo = True  # Teil einer Tastenkombination
            return
        if not ui.view:
            return
        if ui.view == "loading":
            return
        if ui.view == "switcher":
            sw = cc.switcher
            if sw.busy:
                return            # speichert noch – Tasten gehen ans Spiel, hier ignorieren
            dx = 0
            if typ == EV_ABS and code == ABS_HAT0X and value != 0:
                dx = 1 if value > 0 else -1
            elif typ == EV_KEY and code in DPAD:
                dx = DPAD[code][0]
            elif typ == EV_KEY and code in (BTN_TL, BTN_TR):
                dx = -1 if code == BTN_TL else 1
            if dx and sw.items:
                sw.sel = max(0, min(len(sw.items) - 1, sw.sel + dx))
            elif typ == EV_KEY and code == BTN_EAST:      # A
                gs_act(False)
            elif typ == EV_KEY and code == BTN_WEST:      # Y
                gs_act(True)
            elif typ == EV_KEY and code == BTN_SOUTH:     # B
                toggle("switcher")
            state["dirty"] = True
            return
        if ui.view == "power":
            if typ == EV_ABS and code == ABS_HAT0Y and value != 0:
                cc.power_menu.nav(0, 1 if value > 0 else -1)
                state["dirty"] = True
            elif typ == EV_ABS and code == ABS_HAT0X and value != 0:
                cc.power_menu.nav(1 if value > 0 else -1, 0)
                state["dirty"] = True
            elif typ == EV_KEY and code in DPAD:
                dx, dy = DPAD[code]
                if dx or dy:
                    cc.power_menu.nav(dx, dy)
                    state["dirty"] = True
            elif typ == EV_KEY and code == BTN_EAST and value == 1:   # A
                keep = cc.power_menu.confirm()
                if not keep:
                    toggle("power")
                state["dirty"] = True
            elif typ == EV_KEY and code == BTN_NORTH and value == 1:  # X → Details/Untermenü
                cc.power_menu.details()
                state["dirty"] = True
            elif typ == EV_KEY and code == BTN_SOUTH and value == 1:  # B
                if not cc.power_menu.cancel():
                    toggle("power")
                state["dirty"] = True
            return
        if typ == EV_ABS and code in (ABS_HAT0X, ABS_HAT0Y):
            d = 1 if value > 0 else -1
            cc.nav(d, 0) if code == ABS_HAT0X else cc.nav(0, d)
        elif typ == EV_KEY and code in DPAD:
            cc.nav(*DPAD[code])
        elif typ == EV_KEY and code == BTN_SOUTH:
            if not cc.back():
                toggle(ui.view)
                return
        elif typ == EV_KEY and code in (BTN_NORTH, BTN_WEST):
            cc.details()
        elif typ == EV_KEY and code == BTN_EAST:
            result = cc.confirm()
            if result == "power":
                toggle("power")
            elif result == "close":
                toggle("cc")
                return
            elif result == "quit":
                do_quit()
                return
        elif typ == EV_KEY and code in (BTN_TL, BTN_TR):
            if cc.kbd:
                cc.kbd.toggle_shift() if code == BTN_TL else cc.kbd.toggle_layer()
            else:
                cc.turn_page(-1 if code == BTN_TL else 1)
        elif typ == EV_KEY and code == BTN_START and cc.kbd:
            cc.kbd.ok()
        elif typ == EV_KEY and code == BTN_SELECT and cc.kbd and cc.kbd.secret:
            cc.kbd.show = not cc.kbd.show
        elif typ == EV_KEY and code not in KNOWN_UNUSED:
            log("Taste ohne Funktion:", code)
            return
        else:
            return
        state["dirty"] = True

    def on_term(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, on_term)

    def on_resume(*_):
        """SIGUSR1 vom rds-resume.service nach dem Aufwachen: Power-Menü schließen, Screen an."""
        if ui.pending_view == "power":
            ui.pending_view = None
        if ui.view == "power":
            cc.power_menu.state = cc.power_menu.STATE_MAIN
            cc.power_menu.confirm_es_focus = 0
            ui.hide()
            set_grab(False)
            pauser.resume()
        cc.screen_on()   # unteren Screen nach Suspend wieder an
        state["dirty"] = True
    signal.signal(signal.SIGUSR1, on_resume)

    log("bereit – Anbernic-Taste: Kontrollcenter, Home-Taste: Gameswitcher, Strg+C: Ende")
    last_minute = time.strftime("%H:%M")
    next_pad_scan = 0.0
    exit_code = [0]
    wake = {"swallow": False}
    last_game = {"pid": None}
    try:
        while True:
            if time.monotonic() >= next_pad_scan:
                scan_pads()
                next_pad_scan = time.monotonic() + 2
                if not ui.view:
                    g = running_game()
                    pid = g["pid"] if g else None
                    if pid != last_game["pid"]:
                        if g:
                            try:
                                cc.switcher.remember(g)
                            except Exception as exc:
                                log("Gameswitcher: Merken fehlgeschlagen:", exc)
                        if g and g["emu"] in AUTO_DIM_EMUS:
                            cc.screen_off()
                            cc.screen_auto = True
                        elif not g and cc.screen_auto:
                            cc.screen_on()
                        last_game["pid"] = pid
            fds = [fd for fd in [home, pwr, tfd] + list(pads) if fd is not None]
            scrolling = ui.view == "cc" and cc.page == 0 and not cc.sub and cc.marquee
            busy = stick["dir"] or (cc.kbd and cc.kbd.hold) or scrolling or cc.switcher.busy or cc.loading
            for fd in ui.pump(0.05 if busy else 0.5 if cc.sub else 1.0, fds):
                try:
                    if fd == tfd:
                        for ev in read_events(fd, (EV_SYN, EV_KEY, EV_ABS)):
                            t = touch.feed(*ev)
                            if t and ui.view and ui.size:
                                if cc.screen_bottom_off:
                                    continue   # Touch ignorieren wenn Screen aus
                                px, py = touch.to_surface(t[1], t[2], *ui.size)
                                on_touch(t[0], px, py)
                        continue
                    try:
                        events = read_events(fd)
                    except OSError:          # Controller ausgeschaltet/getrennt
                        drop_pad(fd)
                        continue
                    for typ, code, value in events:
                        if fd == home:
                            if typ == EV_KEY and code == BTN_Z and value == 1:
                                toggle("switcher")
                        elif fd == pwr:
                            KEY_POWER = 116
                            if typ == EV_KEY and code == KEY_POWER:
                                if value == 1:
                                    pwr_down_at = time.monotonic()
                                elif value == 0 and pwr_down_at is not None:
                                    held_ms = (time.monotonic() - pwr_down_at) * 1000
                                    pwr_down_at = None
                                    if held_ms < POWER_LONG_MS:
                                        toggle("power")
                                    else:
                                        log("Power: langer Druck → suspend")
                                        if ui.view == "power":
                                            toggle("power")
                                        ui.pending_view = None
                                        subprocess.Popen(["systemctl", "suspend"])
                        elif fd in pads:
                            # Nur Anbernic-Taste weckt unteren Screen auf
                            if typ == EV_KEY and code == BTN_MODE and (cc.screen_bottom_off or wake["swallow"]):
                                if value == 1 and cc.screen_bottom_off:
                                    auto = cc.screen_auto
                                    cc.screen_on()
                                    if auto:   # RetroArch: direkt das CC zeigen
                                        toggle("cc")
                                        cc.redim = True
                                    wake["swallow"] = True   # Loslassen nicht als CC-Aufruf werten
                                elif value == 0:
                                    wake["swallow"] = False
                                continue
                            handle_joy(typ, code, value, pads[fd])
                except Exception:
                    # ein Fehler darf das Kontrollcenter nicht beenden
                    log("Fehler (Kontrollcenter läuft weiter):\n" + traceback.format_exc().rstrip())
                    state["dirty"] = True
            if ui.pending_view and ui.current_output():
                # Bildschirm war kurz weg (z. B. beim Hochfahren aus- und eingeschaltet): wieder anzeigen
                view, ui.pending_view = ui.pending_view, None
                ui.show(view)
            if stick["dir"] and cc.kbd and ui.view and time.monotonic() >= stick["next"]:
                cc.kbd.cursor(stick["dir"])
                stick["next"] = time.monotonic() + 0.12
                state["dirty"] = True
            if ui.view == "cc":
                cc.tick()
                if cc.changed:
                    cc.changed = False
                    state["dirty"] = True
                if time.monotonic() - cc.status_at > 5:
                    cc.refresh()
                    state["dirty"] = True
                if time.strftime("%H:%M") != last_minute:
                    last_minute = time.strftime("%H:%M")
                    state["dirty"] = True
            if scrolling:
                state["dirty"] = True
            if cc.loading:
                sw = cc.switcher
                if getattr(sw, "done", False) or time.monotonic() - cc.loading_t0 > 40:
                    cc.loading = None
                    ui.hide_top()
                    if ui.view == "loading":
                        ui.hide()
                    g = running_game()   # RetroArch/PortMaster: unteren Screen wieder abdunkeln
                    if g and g["emu"] in AUTO_DIM_EMUS:
                        cc.screen_off()
                        cc.screen_auto = True
                else:
                    state["dirty"] = True
            sw = cc.switcher
            if sw.ready:
                sw.ready = False
                sw.busy = None
                sw.load()
                sw.sel = 0
                if ui.view == "switcher":
                    pauser.pause(cc.game)
                    set_grab(True)
                state["dirty"] = True
            if state["dirty"]:
                state["dirty"] = False
                ui.redraw()
    except KeyboardInterrupt:
        pass
    except ConnectionError as exc:
        log(str(exc), "– beende, der Dienst startet neu")
        exit_code[0] = 1
    finally:
        set_grab(False)
        pauser.resume()            # ein Spiel nie eingefroren zurücklassen
        if ui.view:
            try:
                ui.hide()
            except Exception:
                pass
        log("beendet")
    if exit_code[0]:
        sys.exit(exit_code[0])


if __name__ == "__main__":
    main()
