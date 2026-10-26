#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""RetroDualStation – Korrekturen für InputPlumber (ROCKNIX ab 10/2026). Läuft beim Start vor InputPlumber.

1. Home-Taste (RG DS / RG DS Plus): ROCKNIX-Zuordnung anbernic_rgds.yaml ordnet BTN_BACK „gamepad: button: KeyF1“ zu →
   InputPlumber verwirft die Taste („Invalid or unimplemented button: KeyF1“). Richtig: „keyboard: KeyF1“.
2. Phantom-Stick (nur RG DS Plus): adc-joystick liefert neben X/Y auch RX/RY (RX = -Y, RY = X) → InputPlumber-Filter
   „events: exclude: Gamepad:Axis:RightStick“ am adc-joystick.
3. Stick-Kalibrierung: Min/Max des adc-joystick um die gemessene Ruhelage (tools/rds-stickcal.sh → rds-stickcal.txt);
   InputPlumber liest die Werte beim Start.

Die ROCKNIX-Dateien liegen auf schreibgeschütztem squashfs → korrigierte Kopien in /storage, per Bind-Mount eingeblendet
(nur solange der Fehler in ROCKNIX noch drin ist). Aufruf: rds_inputfix.py [an|aus]"""
import fcntl
import glob
import os
import struct
import subprocess
import sys
import time

MAP = "/usr/share/inputplumber/capability_maps/anbernic_rgds.yaml"
DEV = "/usr/share/inputplumber/devices/02-rg-ds-plus.yaml"
DIR = "/storage/.config/retrodualstation/inputplumber"
CAL = "/storage/.config/rds-stickcal.txt"
ORIG = os.path.join(DIR, "abs-original.txt")
LOG = "/storage/.config/retrodualstation/rds-inputfix.log"
HOME_BAD = "      gamepad:\n        button: KeyF1"
HOME_OK = "      keyboard: KeyF1"
JOY_SRC = "      name: adc-joystick\n      handler: event*\n"
JOY_FILTER = "    events:\n      exclude:\n        - Gamepad:Axis:RightStick\n"
AXES = {"X": 0, "Y": 1}


def log(*a):
    line = time.strftime("%d.%m. %H:%M:%S ") + " ".join(str(x) for x in a)
    print(line)
    try:
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def mounted(path):
    try:
        return any(l.split()[1] == path for l in open("/proc/mounts"))
    except OSError:
        return False


def unbind(path):
    if mounted(path):
        subprocess.run(["umount", path], check=False)


def bind(fixed, target):
    if subprocess.run(["mount", "--bind", fixed, target]).returncode == 0:
        return True
    log("Bind-Mount fehlgeschlagen:", target)
    return False


def model():
    try:
        return open("/proc/device-tree/model").read().strip("\0\n ")
    except OSError:
        return ""


def joy_node(wait=0.0):
    end = time.time() + wait
    while True:
        for p in sorted(glob.glob("/sys/class/input/event*/device/name")):
            try:
                if open(p).read().strip() != "adc-joystick":
                    continue
            except OSError:
                continue
            ev = p.split("/")[4]
            for d in ("/dev/input/", "/dev/inputplumber/sources/"):
                if os.path.exists(d + ev):
                    return d + ev
        if time.time() >= end:
            return None
        time.sleep(0.2)


def absinfo(fd, code, new=None):
    if new is not None:
        fcntl.ioctl(fd, 0x401845c0 + code, struct.pack("6i", *new))   # EVIOCSABS
    buf = bytearray(24)
    fcntl.ioctl(fd, 0x80184540 + code, buf)                            # EVIOCGABS
    return list(struct.unpack("6i", buf))


def read_cal(path):
    cal = {}
    try:
        for line in open(path):
            p = line.split()
            if len(p) == 3 and p[0] in AXES:
                lo, hi = int(p[1]), int(p[2])
                if 0 <= lo < hi <= 4096 and hi - lo >= 300:      # Plausibilität
                    cal[p[0]] = (lo, hi)
    except (OSError, ValueError):
        pass
    return cal


def fix_files():
    changed = False
    os.makedirs(DIR, exist_ok=True)
    unbind(MAP)
    if os.path.exists(MAP):
        s = open(MAP).read()
        if HOME_BAD in s:
            fixed = os.path.join(DIR, "anbernic_rgds.yaml")
            open(fixed, "w").write(s.replace(HOME_BAD, HOME_OK))
            if bind(fixed, MAP):
                log("Home-Taste: korrigierte Zuordnung eingeblendet (gamepad KeyF1 → keyboard KeyF1)")
                changed = True
        else:
            log("Home-Taste: ROCKNIX-Zuordnung in Ordnung – nichts zu tun")
    unbind(DEV)
    if "RG DS Plus" in model() and os.path.exists(DEV):
        s = open(DEV).read()
        if JOY_SRC in s and "Gamepad:Axis:RightStick" not in s:
            fixed = os.path.join(DIR, "02-rg-ds-plus.yaml")
            open(fixed, "w").write(s.replace(JOY_SRC, JOY_SRC + JOY_FILTER, 1))
            if bind(fixed, DEV):
                log("RG DS Plus: Phantom-Stick (RX/RY) gefiltert")
                changed = True
    return changed


def apply_cal(restore=False):
    cal = read_cal(ORIG if restore else CAL)
    if not cal:
        return False
    node = joy_node(wait=5.0)
    if not node:
        log("Stick: adc-joystick nicht gefunden – Kalibrierung nicht gesetzt")
        return False
    fd = os.open(node, os.O_RDWR | os.O_NONBLOCK)
    try:
        if not restore and not os.path.exists(ORIG):
            with open(ORIG, "w") as f:
                for name, code in AXES.items():
                    v = absinfo(fd, code)
                    f.write("%s %d %d\n" % (name, v[1], v[2]))
        done = []
        for name, (lo, hi) in cal.items():
            v = absinfo(fd, AXES[name])
            if (v[1], v[2]) != (lo, hi):
                v[1], v[2] = lo, hi
                absinfo(fd, AXES[name], v)
                done.append("%s %d..%d" % (name, lo, hi))
    finally:
        os.close(fd)
    if done:
        log("Stick:", "Original" if restore else "Kalibrierung", "gesetzt –", ", ".join(done))
    return bool(done)


def inputplumber_active():
    return subprocess.run(["systemctl", "is-active", "--quiet", "inputplumber"]).returncode == 0


def main():
    if not os.path.exists("/usr/bin/inputplumber"):
        return
    mode = sys.argv[1] if len(sys.argv) > 1 else "an"
    was_active = inputplumber_active()
    if mode == "aus":
        unbind(MAP)
        unbind(DEV)
        changed = apply_cal(restore=True)
        log("InputPlumber-Korrekturen aus")
        changed = True
    else:
        changed = fix_files()
        changed = apply_cal() or changed
    if was_active and changed:                 # läuft schon (manueller Aufruf/Installation) → Werte neu einlesen
        subprocess.run(["systemctl", "restart", "inputplumber"], check=False)
        log("InputPlumber neu gestartet")


if __name__ == "__main__":
    main()
