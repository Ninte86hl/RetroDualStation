#!/bin/bash
# Analog-Sticks am virtuellen InputPlumber-Gamepad messen (je Richtung Min/Max der Achsen).
# Aufruf vom PC:  ssh -t root@IP 'bash /storage/rds-sticktest.sh'   – Ergebnis: /storage/rds-sticktest.txt
OUT=/storage/rds-sticktest.txt
exec > >(tee "$OUT") 2>&1
cat > /tmp/rds-sticktest.py <<'PY'
import fcntl, glob, os, select, struct, time
EV = struct.Struct("llHHi")
NAMES = {0: "X", 1: "Y", 2: "L2", 3: "RX", 4: "RY", 5: "R2", 16: "HatX", 17: "HatY"}
pads = []
for p in sorted(glob.glob("/sys/class/input/event*/device/name")):
    ev = p.split("/")[4]
    if os.path.exists("/sys/class/input/%s/device" % ev) and any(x.startswith("js") for x in os.listdir("/sys/class/input/%s/device" % ev)):
        pads.append(("/dev/input/" + ev, open(p).read().strip()))
print("Gamepads:", pads)
dev = next((d for d, n in pads if "DualSense" in n and "Motion" not in n), pads[0][0] if pads else None)
if not dev:
    raise SystemExit("Kein Gamepad gefunden")
fd = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
def cur(c):
    b = bytearray(24); fcntl.ioctl(fd, 0x80184540 + c, b); return struct.unpack("6i", b)[:3]
print("Gerät:", dev)
print("Ruhe:", {NAMES[c]: cur(c)[0] for c in (0, 1, 3, 4)})
for what in ("LINKER Stick ganz nach OBEN", "LINKER Stick ganz nach UNTEN", "LINKER Stick ganz nach LINKS",
             "LINKER Stick ganz nach RECHTS", "LINKER Stick einmal im KREIS", "RECHTER Stick ganz nach OBEN",
             "RECHTER Stick ganz nach RECHTS", "Stick LOSLASSEN (nichts berühren)"):
    input(">>> %s: Enter, dann 3 s lang halten/bewegen " % what)
    try:
        while os.read(fd, 4096): pass
    except BlockingIOError:
        pass
    mm, end, n = {}, time.time() + 3, 0
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.1)
        if not r:
            continue
        try:
            data = os.read(fd, EV.size * 64)
        except BlockingIOError:
            continue
        for i in range(0, len(data) - EV.size + 1, EV.size):
            _s, _u, t, c, v = EV.unpack_from(data, i)
            if t == 3 and c in NAMES:
                lo, hi = mm.get(c, (v, v)); mm[c] = (min(lo, v), max(hi, v)); n += 1
    print("   %s → %s (%d Werte)" % (what, "  ".join("%s %d..%d" % (NAMES[c], lo, hi) for c, (lo, hi) in sorted(mm.items())) or "keine Bewegung", n))
print("Nachher Ruhe:", {NAMES[c]: cur(c)[0] for c in (0, 1, 3, 4)})
PY
python3 -u /tmp/rds-sticktest.py < /dev/tty
echo "Fertig – Ergebnis: $OUT"
