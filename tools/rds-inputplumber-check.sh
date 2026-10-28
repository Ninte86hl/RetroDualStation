#!/bin/bash
# InputPlumber-Details für RDS (ROCKNIX-Nightly): Tastenzuordnung, virtuelles Gamepad, Home-Taste, Steuerkreuz.
# Aufruf vom PC:  ssh -t root@IP 'bash /storage/rds-inputplumber-check.sh'   – Ergebnis: /storage/rds-inputplumber-check.txt
OUT=/storage/rds-inputplumber-check.txt
exec > >(tee "$OUT") 2>&1
h() { echo; echo "===== $* ====="; }

h "Zuordnungsdateien (capability maps)"
for d in /usr/share/inputplumber/capability_maps /etc/inputplumber/capability_maps.d /storage/.config/inputplumber; do
    ls "$d" 2>/dev/null | grep -i -E "anbernic|rgds|rg-ds" | while read -r f; do
        echo "--- $d/$f"; grep -v -E "^ *#|^ *$" "$d/$f"
    done
done

h "ROCKNIX-Einstellungen / Dienst"
grep -i -E "inputplumber|gamepad|controller" /storage/.config/system/configs/system.cfg 2>/dev/null | head
systemctl cat inputplumber 2>/dev/null | grep -E "^(ExecStart|Environment|ConditionPath)"
ls /storage/.config/inputplumber /etc/inputplumber 2>/dev/null

h "Virtuelle Geräte (Sysfs-Pfad, Phys, Uniq)"
for e in /sys/class/input/event*; do
    n=$(cat $e/device/name); p=$(readlink -f $e/device)
    printf "%s | %s | phys=%s uniq=%s | %s\n" "${e##*/}" "$n" "$(cat $e/device/phys 2>/dev/null)" "$(cat $e/device/uniq 2>/dev/null)" "$p"
done

h "Fähigkeiten der Gamepads (Tasten / Achsen)"
cat > /tmp/rds-caps.py <<'PY'
import fcntl, glob, os, struct
def bits(fd, ev, n):
    buf = bytearray(n // 8 + 1)
    try:
        fcntl.ioctl(fd, 0x80004520 + ev + (len(buf) << 16), buf)
    except OSError:
        return []
    return [i for i in range(n) if buf[i // 8] >> (i % 8) & 1]
def absinfo(fd, c):
    b = bytearray(24); fcntl.ioctl(fd, 0x80184540 + c, b); return struct.unpack("6i", b)[:3]
for p in sorted(glob.glob("/sys/class/input/event*/device/name")):
    name = open(p).read().strip()
    ev = p.split("/")[4]
    if not os.path.exists("/sys/class/input/%s/device" % ev) or not any(x.startswith("js") for x in os.listdir("/sys/class/input/%s/device" % ev)):
        if "keyboard" not in name.lower() and "keys" not in name.lower():
            continue
    fd = os.open("/dev/input/" + ev, os.O_RDONLY | os.O_NONBLOCK)
    keys = bits(fd, 1, 768); axes = bits(fd, 3, 64)
    print("%s (%s)\n   Tasten: %s\n   Achsen: %s" % (ev, name, keys, ["%d%s" % (a, absinfo(fd, a)) for a in axes]))
    os.close(fd)
PY
python3 /tmp/rds-caps.py

h "Tasten (Enter, dann innerhalb von 4 s drücken)"
cat > /tmp/rds-keytest2.py <<'PY'
import glob, os, select, struct, time
EV = struct.Struct("llHHi")
devs = {}
for p in sorted(glob.glob("/sys/class/input/event*/device/name")):
    node = "/dev/input/" + p.split("/")[4]
    try:
        devs[os.open(node, os.O_RDONLY | os.O_NONBLOCK)] = "%s (%s)" % (node, open(p).read().strip())
    except OSError:
        pass
for what, sec in (("HOME kurz", 4), ("HOME lang halten (2 s)", 5), ("ANBERNIC + X", 4), ("Steuerkreuz HOCH", 4),
                  ("Steuerkreuz LINKS", 4), ("L2", 4), ("R2", 4), ("Lautstärke +", 4), ("Linker Stick nach oben", 4)):
    input(">>> %s: Enter, dann drücken " % what)
    for fd in devs:
        try:
            while os.read(fd, 4096): pass
        except BlockingIOError:
            pass
    seen, end = [], time.time() + sec
    while time.time() < end:
        r, _, _ = select.select(list(devs), [], [], 0.1)
        for fd in r:
            try:
                data = os.read(fd, EV.size * 64)
            except BlockingIOError:
                continue
            for i in range(0, len(data) - EV.size + 1, EV.size):
                _s, _u, t, c, v = EV.unpack_from(data, i)
                if t == 1 and v in (1, 2):
                    seen.append("%s: KEY %d%s" % (devs[fd].split(" ")[0], c, " (wiederholt)" if v == 2 else ""))
                elif t == 3 and c not in (0, 1, 3, 4) and v != 0:
                    seen.append("%s: ABS %d" % (devs[fd].split(" ")[0], c))
                elif t == 3 and c in (0, 1, 3, 4) and abs(v) > 20000:
                    seen.append("%s: ABS %d stark" % (devs[fd].split(" ")[0], c))
    print("   %s → %s" % (what, "; ".join(dict.fromkeys(seen)) or "nichts erkannt"))
PY
python3 -u /tmp/rds-keytest2.py < /dev/tty

h "InputPlumber-Protokoll (Fehler/Warnungen)"
journalctl -u inputplumber --no-pager 2>/dev/null | grep -i -E "warn|error|home|capabilit|anbernic" | tail -15
echo; echo "Fertig – Ergebnis: $OUT"
