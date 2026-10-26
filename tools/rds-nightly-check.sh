#!/bin/bash
# Prüfung einer neuen ROCKNIX-Version für RDS (Eingabe, Anbernic-Taste, Bildschirme, Touch, Ton, DraStic, ES).
# Aufruf vom PC:  ssh -t root@IP 'bash /storage/rds-nightly-check.sh'   – Ergebnis: /storage/rds-nightly-check.txt
# Fragt zwischendurch nach Tastendrücken (Anbernic, Home, L3) – jeweils Enter, dann innerhalb von 4 s drücken.
OUT=/storage/rds-nightly-check.txt
export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock XDG_RUNTIME_DIR=/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1
exec > >(tee "$OUT") 2>&1
h() { echo; echo "===== $* ====="; }

h "System"
grep -E "OS_VERSION|BUILD_DATE|BUILD_BRANCH" /etc/os-release
. /etc/profile >/dev/null 2>&1; echo "QUIRK_DEVICE=$QUIRK_DEVICE"
cat /proc/device-tree/model 2>/dev/null; echo
[ -f /storage/rds-install/VERSION ] && echo "RDS: $(cat /storage/rds-install/VERSION)" || echo "RDS: nicht installiert"

h "Eingabegeräte (/proc/bus/input/devices)"
grep -E "^N:|^H:" /proc/bus/input/devices | paste - - | sed 's/N: Name=//; s/H: Handlers=/ → /'

h "InputPlumber"
systemctl is-active inputplumber 2>/dev/null; pidof inputplumber >/dev/null && echo "läuft (pid $(pidof inputplumber))"
ls /storage/.config/inputplumber 2>/dev/null; ls /usr/share/inputplumber/devices 2>/dev/null | grep -i -E "anbernic|rg" | head

h "Sway: Eingaben"
swaymsg -t get_inputs --raw | python3 -c 'import json,sys
for i in json.load(sys.stdin): print(i["type"], "|", i["identifier"], "|", i.get("libinput",{}).get("calibration_matrix",""))'

h "Sway: Ausgänge"
swaymsg -t get_outputs --raw | python3 -c 'import json,sys
for o in json.load(sys.stdin): print(o["name"], o["rect"], "transform", o.get("transform"))'
grep -n -i -E "drastic|dsperate|touch|map_to|RetroDualStation|input " /storage/.config/sway/config | head -30

h "Tasten (bitte nach Aufforderung drücken)"
python3 - <<'PY'
import glob, os, select, struct, time
EV = struct.Struct("llHHi")
devs = {}
for p in sorted(glob.glob("/sys/class/input/event*/device/name")):
    node = "/dev/input/" + p.split("/")[4]
    try:
        devs[os.open(node, os.O_RDONLY | os.O_NONBLOCK)] = "%s (%s)" % (node, open(p).read().strip())
    except OSError:
        pass
for what in ("ANBERNIC-Taste", "HOME-Taste", "L3", "POWER kurz"):
    input(">>> %s: Enter, dann innerhalb von 4 s einmal drücken " % what)
    for fd in devs:
        try:
            while os.read(fd, 4096): pass
        except BlockingIOError:
            pass
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
    print("   %s → %s" % (what, "; ".join(dict.fromkeys(seen)) or "nichts erkannt"))
PY

h "Touch-Geräte"
for p in /sys/class/input/event*/device/name; do n=$(cat $p); case "$n" in *[Tt]ouch*|*oodix*) echo "$(echo $p | cut -d/ -f5): $n";; esac; done

h "Ton / Mikrofon"
cat /proc/asound/cards
wpctl status 2>/dev/null | sed -n "/Sources:/,/Filters/p" | head -5

h "DraStic"
grep -n -E "DSHOOK|LD_PRELOAD|gptokeyb|follow|fix_main" /usr/bin/start_drastic.sh
strings /usr/lib/libdrastouch.so 2>/dev/null | grep DSHOOK
C=/storage/.config/drastic/config/drastic.cfg
[ -f $C ] && grep -E "^screen_orientation|^threaded_3d|^savestate_number|CONTROL_INDEX_(MENU|SAVE_STATE|LOAD_STATE|QUIT|SWAP_SCREENS|FAKE_MICROPHONE)\]" $C

h "DSperate"
dsperate --version 2>/dev/null | head -2; ls -l /usr/bin/dsperate* 2>/dev/null

h "ES"
ps -o pid,args | grep -E "[e]mulationstation" | head -3
ls -l /usr/bin/emulationstation /storage/rds-install/emulationstation-rgds 2>/dev/null
for b in /usr/bin/emulationstation /storage/rds-install/emulationstation-rgds; do [ -f $b ] && echo "$b fehlende Bibliotheken: $(ldd $b 2>&1 | grep -c 'not found')"; done

h "Kontrollcenter"
systemctl is-active rds-controlcenter 2>/dev/null; journalctl -u rds-controlcenter --no-pager 2>/dev/null | grep -i -E "fehler|error|traceback|nicht gefunden|joypad" | tail -8

h "CPU"
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies 2>/dev/null
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null
echo; echo "Fertig – Ergebnis: $OUT"
