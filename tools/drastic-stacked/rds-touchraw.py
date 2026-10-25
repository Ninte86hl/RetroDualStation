#!/usr/bin/env python3
"""Rohwerte der Touchscreens (direkt vom Kernel, ohne Sway/SDL) – geführt, mit Eingaben je Schritt.
Aufruf vom PC:  ssh -t root@IP 'python3 /storage/rds-stest/rds-touchraw.py'
Für jede Stelle: tippen, Enter – zeigt Gerät (eventN) und Rohposition. Ergebnis: /storage/rds-stest/touchraw.txt"""
import fcntl
import glob
import os
import select
import struct
import time

OUT = "/storage/rds-stest/touchraw.txt"
EV_ABS, ABS_X, ABS_Y, ABS_MT_X, ABS_MT_Y = 3, 0x00, 0x01, 0x35, 0x36
EVENT = struct.Struct("llHHi")


def absinfo(fd, code):
    buf = bytearray(24)
    try:
        fcntl.ioctl(fd, 0x80184540 + code, buf)
        val, mn, mx = struct.unpack("6i", buf)[:3]
        return mn, mx
    except OSError:
        return None


devs = {}
for p in sorted(glob.glob("/sys/class/input/event*/device/name")):
    name = open(p).read().strip()
    if "goodix" in name.lower() or "touch" in name.lower():
        node = "/dev/input/" + p.split("/")[4]
        fd = os.open(node, os.O_RDONLY | os.O_NONBLOCK)
        devs[fd] = node
        phys = (open(p.replace("/name", "/phys")).read().strip() if os.path.exists(p.replace("/name", "/phys")) else "")
        print("%s  %s  phys=%s  X%s Y%s MT-X%s MT-Y%s" % (node, name, phys, absinfo(fd, ABS_X), absinfo(fd, ABS_Y),
                                                          absinfo(fd, ABS_MT_X), absinfo(fd, ABS_MT_Y)))
if not devs:
    raise SystemExit("Kein Touchscreen gefunden")

lines = ["=== Touch-Rohwerte %s ===" % time.strftime("%d.%m. %H:%M")]
lines += ["%s" % n for n in devs.values()]


def drain():
    for fd in devs:
        try:
            while os.read(fd, EVENT.size * 64):
                pass
        except BlockingIOError:
            pass


def collect(seconds=0.4):
    """Erste Position je Gerät aus den Ereignissen seit dem letzten drain."""
    got = {}
    end = time.time() + seconds
    while time.time() < end:
        r, _, _ = select.select(list(devs), [], [], 0.05)
        for fd in r:
            try:
                data = os.read(fd, EVENT.size * 64)
            except BlockingIOError:
                continue
            for i in range(0, len(data) - EVENT.size + 1, EVENT.size):
                _s, _u, typ, code, val = EVENT.unpack_from(data, i)
                if typ == EV_ABS and code in (ABS_X, ABS_Y, ABS_MT_X, ABS_MT_Y):
                    d = got.setdefault(devs[fd], {})
                    d.setdefault({ABS_X: "x", ABS_MT_X: "x", ABS_Y: "y", ABS_MT_Y: "y"}[code], val)
    return got


SPOTS = ["UNTEN links oben", "UNTEN rechts oben", "UNTEN links unten", "UNTEN rechts unten", "UNTEN Mitte",
         "OBEN links oben", "OBEN rechts oben", "OBEN links unten", "OBEN rechts unten", "OBEN Mitte"]
print("\nJeweils EINMAL kurz an die Stelle tippen (etwas vom Rand weg), dann Enter.\n")
for spot in SPOTS:
    drain()
    input(">>> %s antippen, dann Enter " % spot)
    got = collect()
    txt = "  ".join("%s x=%s y=%s" % (n, v.get("x"), v.get("y")) for n, v in got.items()) or "(nichts)"
    print("    " + txt)
    lines.append("%-20s %s" % (spot, txt))

with open(OUT, "w") as f:
    f.write("\n".join(lines) + "\n")
print("\nGespeichert: %s" % OUT)
