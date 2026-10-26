#!/bin/bash
# Versuch: Home-Taste RG DS / RG DS Plus unter InputPlumber (ROCKNIX-Nightly ab 10/2026).
# Fehler in ROCKNIX: anbernic_rgds.yaml ordnet BTN_BACK (Home) „gamepad: button: KeyF1“ zu → InputPlumber meldet
# „Invalid or unimplemented button: KeyF1“ und die Taste kommt nirgends an. Richtig wäre „keyboard: KeyF1“
# (so steht es in anbernic_gen1.yaml / anbernic_arc.yaml).
# Aufruf vom PC:  ssh -t root@IP 'bash /storage/rds-homekey-fix.sh [an|aus|status]'
SRC=/usr/share/inputplumber/capability_maps/anbernic_rgds.yaml
# /etc ist schreibgeschützt (squashfs) → korrigierte Kopie in /storage, per Bind-Mount über die ROCKNIX-Datei gelegt
# (nur bis zum Neustart; das Original bleibt unverändert).
DST=/storage/.config/rds-anbernic_rgds.yaml

test_home() {
    cat > /tmp/rds-hometest.py <<'PY'
import glob, os, select, struct, time
EV = struct.Struct("llHHi")
devs = {}
for p in sorted(glob.glob("/sys/class/input/event*/device/name")):
    try:
        devs[os.open("/dev/input/" + p.split("/")[4], os.O_RDONLY | os.O_NONBLOCK)] = open(p).read().strip()
    except OSError:
        pass
input(">>> HOME: Enter, dann innerhalb von 4 s einmal drücken ")
seen, end = [], time.time() + 4
while time.time() < end:
    r, _, _ = select.select(list(devs), [], [], 0.1)
    for fd in r:
        try:
            data = os.read(fd, EV.size * 64)
        except BlockingIOError:
            continue
        for i in range(0, len(data) - EV.size + 1, EV.size):
            _s, _u, t, c, v = EV.unpack_from(data, i)
            if t == 1 and v == 1:
                seen.append("%s: KEY %d" % (devs[fd], c))
print("   HOME → %s" % ("; ".join(dict.fromkeys(seen)) or "nichts erkannt"))
PY
    python3 -u /tmp/rds-hometest.py < /dev/tty
}

case "${1:-an}" in
an)
    [ -f "$SRC" ] || { echo "$SRC fehlt – andere ROCKNIX-Version?"; exit 1; }
    if grep -q " $SRC " /proc/mounts; then umount "$SRC"; fi
    python3 - "$SRC" "$DST" <<'PY'
import sys
s = open(sys.argv[1]).read()
old = "      gamepad:\n        button: KeyF1"
if old not in s:
    sys.exit("Zuordnung 'gamepad: button: KeyF1' nicht gefunden – evtl. schon behoben")
s = s.replace(old, "      keyboard: KeyF1")
open(sys.argv[2], "w").write(s)
print("Geschrieben:", sys.argv[2])
PY
    [ -f "$DST" ] || exit 1
    mount --bind "$DST" "$SRC" || { echo "Bind-Mount fehlgeschlagen"; exit 1; }
    grep -n "KeyF1" "$SRC"
    systemctl restart inputplumber; sleep 3
    echo "InputPlumber: $(systemctl is-active inputplumber)"
    journalctl -u inputplumber --no-pager --since "-10s" | grep -i -E "error|warn|rds-anbernic|capability" | tail -5
    test_home
    ;;
aus)
    grep -q " $SRC " /proc/mounts && umount "$SRC"
    rm -f "$DST"; systemctl restart inputplumber; sleep 3
    echo "Zurück auf ROCKNIX-Zuordnung · InputPlumber: $(systemctl is-active inputplumber)"
    ;;
status|*)
    grep -q " $SRC " /proc/mounts && echo "RDS-Zuordnung aktiv: $(grep KeyF1 "$SRC")" || echo "Keine RDS-Zuordnung aktiv"
    test_home
    ;;
esac
