#!/bin/bash
# Stick-Kalibrierung RG DS Plus unter InputPlumber (ROCKNIX-Nightly ab 10/2026) – Versuch.
# Befund 26.10.: adc-joystick meldet den Bereich 15..940 (Mitte 477), der Stick ruht aber bei X ~445 / Y ~511 und
# erreicht X 136..926 / Y 105..911. InputPlumber rechnet linear über 15..940 → Mitte verschoben, Ausschlag je Richtung
# 74–80 %; ES reagiert erst ab ~70 % → „träge“. Früher hat der ROCKNIX-Joypad-Treiber die Mitte selbst kalibriert.
# Abhilfe: Min/Max des Kernel-Geräts per EVIOCSABS um die gemessene Ruhelage legen, dann InputPlumber neu starten
# (liest die Werte beim Start). Gilt bis zum Neustart.
# Aufruf vom PC:  ssh -t root@IP 'bash /storage/rds-stickcal.sh [an|aus|status]'
OUT=/storage/rds-stickcal.txt
CAL=/storage/.config/rds-stickcal.txt
exec > >(tee "$OUT") 2>&1
cat > /tmp/rds-stickcal.py <<'PY'
import fcntl, glob, os, struct, sys, time
mode, cal = sys.argv[1], sys.argv[2]
def node(name):
    for p in sorted(glob.glob("/sys/class/input/event*/device/name")):
        if open(p).read().strip() == name:
            ev = p.split("/")[4]
            for d in ("/dev/input/", "/dev/inputplumber/sources/"):
                if os.path.exists(d + ev):
                    return d + ev
    return None
dev = node("adc-joystick")
if not dev:
    sys.exit("adc-joystick nicht gefunden")
fd = os.open(dev, os.O_RDWR | os.O_NONBLOCK)
def get(c):
    b = bytearray(24); fcntl.ioctl(fd, 0x80184540 + c, b); return list(struct.unpack("6i", b))
def put(c, v):
    fcntl.ioctl(fd, 0x401845c0 + c, struct.pack("6i", *v))
AX = {0: "X", 1: "Y"}
print("Gerät:", dev)
for c in AX:
    print("  vorher %s: wert/min/max/fuzz/flat/res = %s" % (AX[c], get(c)))
if mode == "aus":
    for c in AX:
        v = get(c); v[1], v[2] = 15, 940; put(c, v)
    print("Zurück auf 15..940")
elif mode == "an":
    # Ruhelage schwankt je nach Richtung, aus der der Stick zurückfedert (26.10.: X 409..460) → Mittel aus 4 Richtungen
    rest = {c: [] for c in AX}
    for d in ("OBEN", "UNTEN", "LINKS", "RECHTS"):
        while True:
            input(">>> Enter, dann den Stick nach %s drücken und sofort LOSLASSEN (misst 3 s) " % d)
            vals = {c: [] for c in AX}
            end = time.time() + 3
            while time.time() < end:
                for c in AX:
                    vals[c].append(get(c)[0])
                time.sleep(0.02)
            last = {c: sorted(vals[c][-35:])[17] for c in AX}            # Median der letzten ~0,7 s
            moved = any(max(vals[c]) - min(vals[c]) > 150 for c in AX)
            if all(abs(last[c] - 477) < 200 for c in AX) and moved:
                break
            print("    → nicht erkannt (%s) – bitte nochmal" % ("Stick noch gedrückt?" if moved else "keine Bewegung"))
        for c in AX:
            rest[c].append(last[c])
        print("    Ruhe nach %s: X %d  Y %d" % (d, last[0], last[1]))
    mid = {c: sum(rest[c]) // len(rest[c]) for c in AX}
    print("  Mitte: X %d (%d..%d)  Y %d (%d..%d)" % (mid[0], min(rest[0]), max(rest[0]), mid[1], min(rest[1]), max(rest[1])))
    input(">>> Stick 5 s lang mehrmals im KREIS ganz am Rand drehen – Enter, dann los ")
    lo = dict(mid); hi = dict(mid); end = time.time() + 5
    while time.time() < end:
        for c in AX:
            v = get(c)[0]; lo[c] = min(lo[c], v); hi[c] = max(hi[c], v)
        time.sleep(0.01)
    lines = []
    for c in AX:
        half = int(min(mid[c] - lo[c], hi[c] - mid[c]) * 0.92)   # kürzere Seite erreicht sicher 100 %
        if half < 150:
            sys.exit("Zu wenig Ausschlag gemessen (%s: %d..%d, Ruhe %d) – nichts geändert" % (AX[c], lo[c], hi[c], mid[c]))
        v = get(c); v[1], v[2] = mid[c] - half, mid[c] + half; put(c, v)
        print("  %s: Ruhe %d, gemessen %d..%d → neu %d..%d" % (AX[c], mid[c], lo[c], hi[c], v[1], v[2]))
        lines.append("%s %d %d" % (AX[c], v[1], v[2]))
    open(cal, "w").write("\n".join(lines) + "\n")
    print("Gespeichert:", cal)
for c in AX:
    print("  nachher %s: %s" % (AX[c], get(c)))
PY
case "${1:-status}" in
an|aus)
    python3 -u /tmp/rds-stickcal.py "$1" "$CAL" < /dev/tty || exit 1
    [ "$1" = "aus" ] && rm -f "$CAL"
    systemctl restart inputplumber; sleep 3
    echo "InputPlumber: $(systemctl is-active inputplumber) (neu gestartet – liest die Werte neu)"
    grep -q " /usr/share/inputplumber/devices/02-rg-ds-plus.yaml " /proc/mounts \
        && echo "Phantom-Stick-Filter: aktiv" || echo "Phantom-Stick-Filter: NICHT aktiv – erst rds-inputplumber-fix.sh an"
    ;;
*)
    python3 -u /tmp/rds-stickcal.py status "$CAL"
    ;;
esac
echo "Fertig – Ergebnis: $OUT"
