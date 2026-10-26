#!/bin/bash
# Linker Stick: Rohwerte (adc-joystick, Kernel) neben dem, was InputPlumber daraus macht (virtueller DualSense).
# Liest per EVIOCGABS – funktioniert auch, wenn InputPlumber das Gerät für sich beansprucht.
# Aufruf vom PC:  ssh -t root@IP 'bash /storage/rds-stickraw.sh'   – Ergebnis: /storage/rds-stickraw.txt
OUT=/storage/rds-stickraw.txt
exec > >(tee "$OUT") 2>&1
cat > /tmp/rds-stickraw.py <<'PY'
import fcntl, glob, os, struct, time
def find(pred):
    for p in sorted(glob.glob("/sys/class/input/event*/device/name")):
        n = open(p).read().strip()
        if pred(n):
            ev = p.split("/")[4]
            # InputPlumber versteckt Quellgeräte: /dev/input/eventN → /dev/inputplumber/sources/eventN
            for d in ("/dev/input/", "/dev/inputplumber/sources/"):
                if os.path.exists(d + ev):
                    return d + ev, n
            return None, n
    return None, None
def info(fd, c):
    b = bytearray(24)
    try:
        fcntl.ioctl(fd, 0x80184540 + c, b)
    except OSError:
        return None
    return struct.unpack("6i", b)   # value min max fuzz flat resolution
raw, _ = find(lambda n: n == "adc-joystick")
vir, _ = find(lambda n: "DualSense" in n and "Motion" not in n and "Touchpad" not in n and "Jack" not in n)
rfd = os.open(raw, os.O_RDONLY | os.O_NONBLOCK) if raw else None
if not rfd:
    print("adc-joystick-Gerätedatei nicht gefunden:", os.listdir("/dev/inputplumber/sources") if os.path.isdir("/dev/inputplumber/sources") else "-")
vfd = os.open(vir, os.O_RDONLY | os.O_NONBLOCK) if vir else None
print("Roh:", raw, "· Virtuell:", vir)
for c, n in ((0, "X"), (1, "Y"), (3, "RX"), (4, "RY")):
    print("  Roh %-2s %s" % (n, "wert/min/max/fuzz/flat/res = %s" % (info(rfd, c),) if rfd else "-"))
def row():
    r = [info(rfd, c)[0] if rfd and info(rfd, c) else None for c in (0, 1)]
    v = [info(vfd, c)[0] if vfd else None for c in (0, 1)]
    return r, v
def phase(text, secs):
    input("\n>>> %s – Enter, dann %d s " % (text, secs))
    lo, hi, samples = {}, {}, []
    end = time.time() + secs
    while time.time() < end:
        (rx, ry), (vx, vy) = row()
        for k, val in (("rx", rx), ("ry", ry), ("vx", vx), ("vy", vy)):
            if val is not None:
                lo[k] = min(lo.get(k, val), val); hi[k] = max(hi.get(k, val), val)
        samples.append((rx, ry, vx, vy))
        time.sleep(0.05)
    print("   Roh X %s..%s  Y %s..%s   |  Virtuell X %s..%s  Y %s..%s" % (
        lo.get("rx"), hi.get("rx"), lo.get("ry"), hi.get("ry"), lo.get("vx"), hi.get("vx"), lo.get("vy"), hi.get("vy")))
    return samples
phase("Stick NICHT berühren (Ruhe)", 3)
for t in ("ganz nach OBEN halten", "ganz nach UNTEN halten", "ganz nach LINKS halten", "ganz nach RECHTS halten",
          "LANGSAM von Mitte nach OBEN schieben", "zweimal langsam im KREIS am Rand", "loslassen – Ruhe"):
    s = phase(t, 4)
    if t.startswith("LANGSAM"):
        print("   Verlauf Roh-Y → virtuell-Y:", " ".join("%s→%s" % (a[1], a[3]) for a in s[::8]))
PY
python3 -u /tmp/rds-stickraw.py < /dev/tty
echo "Fertig – Ergebnis: $OUT"
