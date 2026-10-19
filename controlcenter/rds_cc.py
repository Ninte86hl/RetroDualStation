#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""RetroDualStation Kontrollcenter – Prototyp 0.1

Zeigt auf dem unteren Bildschirm (DSI-1) eine Fläche auf der Wayland-Overlay-Ebene,
also über ES und über jedem Emulator.

  Anbernic-Taste (allein gedrückt)  -> Kontrollcenter ein/aus
  Return/Home-Taste                 -> Gameswitcher (Platzhalter) ein/aus
  B                                  -> schließen

Nur Python 3 + libwayland-client + libcairo (beides auf ROCKNIX vorhanden).
Start zum Testen über SSH:   python3 rds_cc.py      (Ende mit Strg+C)
"""
import ctypes
import fcntl
import mmap
import os
import select
import struct
import sys
import time
from ctypes import (CDLL, CFUNCTYPE, POINTER, Structure, Union, byref, c_char,
                    c_char_p, c_double, c_int, c_int32, c_uint32, c_void_p, cast,
                    pointer)

OUTPUT_NAME = os.environ.get("RDS_CC_OUTPUT", "DSI-1")
JOYPAD_NAME = os.environ.get("RDS_CC_JOYPAD", "retrogame_joypad")
HOME_NAME = os.environ.get("RDS_CC_HOMEKEY", "adc-keys-back")
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
    "cairo_fill": [c_void_p], "cairo_paint": [c_void_p],
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


def _rgb(hexstr, a=1.0):
    h = hexstr.lstrip("#")
    return int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a


def _round_rect(cr, x, y, w, h, r):
    pi = 3.141592653589793
    cairo.cairo_new_sub_path(cr)
    cairo.cairo_arc(cr, x + w - r, y + r, r, -pi / 2, 0)
    cairo.cairo_arc(cr, x + w - r, y + h - r, r, 0, pi / 2)
    cairo.cairo_arc(cr, x + r, y + h - r, r, pi / 2, pi)
    cairo.cairo_arc(cr, x + r, y + r, r, pi, 3 * pi / 2)
    cairo.cairo_close_path(cr)


def _text(cr, txt, size, x, y, color, bold=False, center=False):
    cairo.cairo_select_font_face(cr, b"sans-serif", 0, 1 if bold else 0)
    cairo.cairo_set_font_size(cr, size)
    data = txt.encode("utf-8")
    if center:
        ext = TextExtents()
        cairo.cairo_text_extents(cr, data, byref(ext))
        x = x - ext.width / 2 - ext.x_bearing
    cairo.cairo_set_source_rgba(cr, *_rgb(color))
    cairo.cairo_move_to(cr, x, y)
    cairo.cairo_show_text(cr, data)


def draw(cr, w, h, view):
    """Prototyp-Inhalt im Stil des freigegebenen Entwurfs (dunkel)."""
    cairo.cairo_set_source_rgba(cr, *_rgb("373737"))
    cairo.cairo_paint(cr)
    cairo.cairo_set_source_rgba(cr, 0, 0, 0, 0.35)
    _round_rect(cr, 36, 32, w - 72, h - 64, 24)
    cairo.cairo_fill(cr)
    title = "Kontrollcenter" if view == "cc" else "Gameswitcher"
    _text(cr, time.strftime("%H:%M"), 120, w / 2, h / 2 - 20, "ffffff", bold=True, center=True)
    _text(cr, "RetroDualStation", 40, w / 2, h / 2 + 50, "ffffff", bold=True, center=True)
    _text(cr, f"{title} · Prototyp 0.1", 24, w / 2, h / 2 + 92, "bdbdbd", center=True)
    hint = "Anbernic-Taste oder B: schließen" if view == "cc" else "Home-Taste oder B: schließen"
    _text(cr, hint, 20, w / 2, h - 70, "bdbdbd", center=True)
    cairo.cairo_set_source_rgba(cr, *_rgb("e5383b"))
    _round_rect(cr, w / 2 - 60, 70, 56, 10, 5)
    cairo.cairo_fill(cr)
    cairo.cairo_set_source_rgba(cr, *_rgb("3d7bff"))
    _round_rect(cr, w / 2 + 4, 70, 56, 10, 5)
    cairo.cairo_fill(cr)


# ------------------------------------------------------------ Overlay-App ----

class Overlay:
    def __init__(self):
        self.display = wl.wl_display_connect(None)
        if not self.display:
            sys.exit("Keine Verbindung zu Wayland (XDG_RUNTIME_DIR/WAYLAND_DISPLAY prüfen)")
        self.compositor = self.shm = self.layer_shell = None
        self.outputs = {}  # proxy -> name
        self.surface = self.lsurf = self.buffer = None
        self.view = None
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

    def _bind(self, name, iface, version):
        return marshal(self.registry, 0, iface, ("u", name), ("s", iface.name),
                       ("u", version), ("n", None), version=version)

    def _on_global(self, _data, _reg, name, iface, version):
        try:
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
        except Exception as exc:  # Callbacks dürfen nie werfen
            log("Fehler in global:", exc)

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

    # -- anzeigen / verbergen --
    def show(self, view):
        if self.surface:
            self.hide()
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

    def _on_configure(self, _d, lsurf, serial, w, h):
        try:
            marshal(lsurf, 6, None, ("u", serial))          # ack_configure
            w, h = w or 1024, h or 768
            self._render(w, h)
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
        draw(cr, w, h, self.view)
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

    def hide(self):
        if self.lsurf:
            marshal(self.lsurf, 7, None, destroy=True)
        if self.surface:
            marshal(self.surface, 0, None, destroy=True)
        if self.buffer:
            marshal(self.buffer, 0, None, destroy=True)
        self.lsurf = self.surface = self.buffer = None
        self.view = None
        wl.wl_display_flush(self.display)
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

EV_KEY = 1
BTN_SOUTH, BTN_MODE, BTN_Z = 304, 316, 309
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


def read_keys(fd):
    try:
        data = os.read(fd, EVENT.size * 64)
    except BlockingIOError:
        return []
    keys = []
    for off in range(0, len(data) - EVENT.size + 1, EVENT.size):
        _s, _us, typ, code, value = EVENT.unpack_from(data, off)
        if typ == EV_KEY:
            keys.append((code, value))
    return keys


def grab(fd, on):
    try:
        fcntl.ioctl(fd, EVIOCGRAB, 1 if on else 0)
    except OSError as exc:
        log("Grab", "an" if on else "aus", "fehlgeschlagen:", exc)


# ------------------------------------------------------------------- main ----

def main():
    ui = Overlay()
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

    log("bereit – Anbernic-Taste: Kontrollcenter, Home-Taste: Gameswitcher, Strg+C: Ende")

    def toggle(view):
        if ui.view == view:
            ui.hide()
            set_grab(False)
        else:
            ui.show(view)          # wechselt auch direkt zwischen den Ansichten
            set_grab(True)

    try:
        while True:
            for fd in ui.pump(1.0, fds):
                for code, value in read_keys(fd):
                    if fd == home and code == BTN_Z and value == 1:
                        toggle("switcher")
                    elif fd == joy:
                        if code == BTN_MODE and value == 1:
                            mode_down, combo = True, False
                        elif code == BTN_MODE and value == 0:
                            if mode_down and not combo:
                                toggle("cc")
                            mode_down = False
                        elif value == 1:
                            if mode_down:
                                combo = True  # Teil einer Tastenkombination
                            elif ui.view and code == BTN_SOUTH:
                                toggle(ui.view)
    except KeyboardInterrupt:
        pass
    finally:
        set_grab(False)
        if ui.view:
            ui.hide()
        log("beendet")


if __name__ == "__main__":
    main()
