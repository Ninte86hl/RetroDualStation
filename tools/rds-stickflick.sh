#!/bin/bash
# Stick-Zuverlässigkeit: je Richtung mehrmals kurz antippen – zeigt pro Antippen den größten Ausschlag (roh und
# virtuell) und ob er die Schwellen erreicht (ES ~70 %, CC 60 %). Aufruf: ssh -t root@IP 'bash /storage/rds-stickflick.sh'
OUT=/storage/rds-stickflick.txt
exec > >(tee "$OUT") 2>&1
echo "--- DraStic-Belegung Richtungen (1152+n = Achse n plus, 1216+n = minus):"
grep -E "CONTROL_INDEX_(UP|DOWN|LEFT|RIGHT)\]" /storage/.config/drastic/config/drastic.cfg
cat > /tmp/rds-stickflick.py <<'PY'
import fcntl, glob, os, struct, time
def find(pred):
    for p in sorted(glob.glob("/sys/class/input/event*/device/name")):
        n = open(p).read().strip()
        if pred(n):
            ev = p.split("/")[4]
            for d in ("/dev/input/", "/dev/inputplumber/sources/"):
                if os.path.exists(d + ev):
                    return d + ev
    return None
def info(fd, c):
    b = bytearray(24); fcntl.ioctl(fd, 0x80184540 + c, b); return struct.unpack("6i", b)
rfd = os.open(find(lambda n: n == "adc-joystick"), os.O_RDONLY | os.O_NONBLOCK)
vfd = os.open(find(lambda n: "DualSense" in n and all(x not in n for x in ("Motion", "Touchpad", "Jack"))), os.O_RDONLY | os.O_NONBLOCK)
print("Roh X", info(rfd, 0)[1:3], "Y", info(rfd, 1)[1:3])
for name, ax, sign in (("LINKS", 0, -1), ("RECHTS", 0, 1), ("OBEN", 1, -1), ("UNTEN", 1, 1)):
    input("\n>>> %s: Enter, dann 8 s lang etwa einmal pro Sekunde kurz nach %s tippen (wie beim Navigieren) " % (name, name))
    print("   Ruhe vorher: roh X %d Y %d · virtuell X %d Y %d" % (info(rfd, 0)[0], info(rfd, 1)[0], info(vfd, 0)[0], info(vfd, 1)[0]))
    flicks, cur, end = [], None, time.time() + 8
    while time.time() < end:
        r = info(rfd, ax)[0]; v = info(vfd, ax)[0]
        n = (v - 127.5) / 127.5 * sign            # 0 = Mitte, 1 = voller Ausschlag in diese Richtung
        if n > 0.25:
            if cur is None:
                cur = [n, r, time.time()]
            elif n > cur[0]:
                cur[0], cur[1] = n, r
        elif cur is not None:
            flicks.append((cur[0], cur[1], time.time() - cur[2])); cur = None
        time.sleep(0.005)
    if cur:
        flicks.append((cur[0], cur[1], time.time() - cur[2]))
    time.sleep(1)
    print("   Ruhe nachher: roh X %d Y %d · virtuell X %d Y %d" % (info(rfd, 0)[0], info(rfd, 1)[0], info(vfd, 0)[0], info(vfd, 1)[0]))
    es = sum(1 for f in flicks if f[0] >= 0.7)
    print("   %d× angetippt, %d× über 70 %% (ES), %d× über 60 %% (CC)" % (len(flicks), es, sum(1 for f in flicks if f[0] >= 0.6)))
    print("   je Tippen max. Ausschlag %%/roh/Dauer: " + "  ".join("%d%%/%d/%.2fs" % (f[0] * 100, f[1], f[2]) for f in flicks))
PY
python3 -u /tmp/rds-stickflick.py < /dev/tty
echo "Fertig – Ergebnis: $OUT"
