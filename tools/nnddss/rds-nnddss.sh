#!/bin/bash
# NNDDSS (Anbernic-Emulator der RG DS Plus Original-Firmware) testweise auf ROCKNIX starten – nur privat, nicht Teil
# von RDS (Anbernic-Software mit DraStic für Android im Kern). Dateien kommen aus der eigenen Original-Firmware.
#
# Aufruf vom PC (vorher NNDDSS_tar.gz nach /storage/ kopieren):
#   ssh -t root@IP 'bash /storage/rds-nnddss.sh einrichten'   entpacken nach /storage/nnddss, Pfade anpassen
#   ssh -t root@IP 'bash /storage/rds-nnddss.sh pruefen'      Bibliotheken, Geräte, Sway
#   ssh -t root@IP 'bash /storage/rds-nnddss.sh start [ROM]'  ohne ROM: eigene Spieleliste von NNDDSS
#   ssh -t root@IP 'bash /storage/rds-nnddss.sh stopp'
#   ssh -t root@IP 'bash /storage/rds-nnddss.sh log'
#   ssh -t root@IP 'bash /storage/rds-nnddss.sh entfernen'    /storage/nnddss löschen (Spielstände bleiben)
#
# Was angepasst wird (nur in der eigenen Kopie):
# - Programm liest /mnt/vendor/oem/board.ini und language.ini (gibt es auf ROCKNIX nicht, /mnt ist schreibgeschützt)
#   → in nnddss.rds auf /tmp/nnddss/oem/… umgebogen (gleich lange Pfade), die Dateien legt „start“ an.
# - config.ini: Spieleordner /storage/roms/nds.
# - Savestates und Spielstände (backup) eigene Ordner unter /storage/nnddss-daten (DraStic-Stände bleiben unberührt).
A=/storage/nnddss
DATA=/storage/nnddss-daten
LOG=/storage/nnddss/nnddss.log
SRC=${SRC:-/storage/NNDDSS_tar.gz}
export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock

touch_dev() {   # unterer Touchscreen (RG DS: fe5e0000.i2c, Plus: einziger Goodix)
    local best="" ev
    for p in /sys/class/input/event*/device/name; do
        grep -qi goodix "$p" || continue
        ev=/dev/input/$(echo "$p" | cut -d/ -f5)
        [ -z "$best" ] && best=$ev
        readlink -f "$(dirname "$p")" | grep -q fe5e0000.i2c && best=$ev
    done
    echo "$best"
}

case "$1" in
einrichten)
    [ -f "$SRC" ] || { echo "$SRC fehlt – erst vom PC kopieren: scp NNDDSS_tar.gz root@IP:/storage/"; exit 1; }
    pidof nnddss.rds >/dev/null && { echo "NNDDSS läuft – erst stoppen"; exit 1; }
    rm -rf /tmp/nnddss-x && mkdir -p /tmp/nnddss-x
    tar xzf "$SRC" -C /tmp/nnddss-x 2>/dev/null
    S=$(dirname "$(find /tmp/nnddss-x -name nnddss -type f -perm -u+x | head -1)")
    [ -x "$S/nnddss" ] || { echo "Programm nnddss im Archiv nicht gefunden"; exit 1; }
    mkdir -p "$A" "$DATA/savestates" "$DATA/backup"
    cp -a "$S/nnddss" "$S/lib" "$S/assets" "$A/"
    mkdir -p "$A/User"
    cp -an "$S/User/." "$A/User/" 2>/dev/null
    B=$(find /tmp/nnddss-x -name board.ini | head -1)
    [ -n "$B" ] && cp "$B" "$A/board.ini"
    L=$(find /tmp/nnddss-x -name language.ini | head -1)
    [ -n "$L" ] && cp "$L" "$A/language.ini"
    rm -rf /tmp/nnddss-x
    python3 - "$A/nnddss" "$A/nnddss.rds" <<'PY'
import sys
d = open(sys.argv[1], "rb").read()
for a, b in ((b"/mnt/vendor/oem/board.ini", b"/tmp/nnddss/oem/board.ini"),
             (b"/mnt/vendor/oem/language.ini", b"/tmp/nnddss/oem/language.ini")):
    assert len(a) == len(b)
    n = d.count(a + b"\0")
    d = d.replace(a + b"\0", b + b"\0")
    print("umgebogen: %s → %s (%d×)" % (a.decode(), b.decode(), n))
open(sys.argv[2], "wb").write(d)
PY
    chmod +x "$A/nnddss.rds"
    for f in "$A/assets/config.ini" "$A/User/config.ini"; do
        [ -f "$f" ] && sed -i -e 's#^games_dir=.*#games_dir=/storage/roms/nds#' -e 's#^browse_dir=.*#browse_dir=/storage/roms/nds#' "$f"
    done
    for d in savestates backup; do rm -rf "$A/User/$d"; ln -s "$DATA/$d" "$A/User/$d"; done
    echo "Eingerichtet: $A ($(du -sh "$A" | cut -f1)) · Spielstände: $DATA"
    echo "Board: $(cat "$A/board.ini" 2>/dev/null)"
    ;;
pruefen)
    echo "--- Bibliotheken:"
    LD_LIBRARY_PATH=$A/lib:/usr/lib ldd "$A/nnddss.rds" 2>&1 | grep -E "not found|SDL|EGL|GLES|libc\.so" || echo "ldd fehlt"
    ls /usr/lib/libSDL2_ttf* /usr/lib/libSDL2-2.0* 2>/dev/null
    echo "--- glibc: $(ldd --version 2>&1 | head -1)"
    echo "--- Touch: $(touch_dev)"
    echo "--- Sway-Ausgänge:"; swaymsg -t get_outputs --raw | python3 -c 'import json,sys; [print(" ", o["name"], o["rect"]) for o in json.load(sys.stdin)]'
    echo "--- Gamepads:"; grep -h "" /sys/class/input/js*/device/name 2>/dev/null
    ;;
start)
    [ -x "$A/nnddss.rds" ] || { echo "Erst einrichten"; exit 1; }
    pidof nnddss.rds >/dev/null && { echo "läuft schon"; exit 1; }
    pidof drastic >/dev/null && { echo "DraStic läuft – erst beenden"; exit 1; }
    mkdir -p /tmp/nnddss/oem
    cp "$A/board.ini" /tmp/nnddss/oem/board.ini 2>/dev/null || printf RGdsplus2 > /tmp/nnddss/oem/board.ini
    cp "$A/language.ini" /tmp/nnddss/oem/language.ini 2>/dev/null || : > /tmp/nnddss/oem/language.ini
    ROM=""
    if [ -n "$2" ]; then
        ROM=$(ls /storage/roms/nds/* 2>/dev/null | grep -i -E "\.(nds|zip|7z)$" | grep -i -- "$2" | head -1)
        [ -n "$ROM" ] || { echo "Keine ROM zu: $2"; exit 1; }
    fi
    TD=$(touch_dev)
    echo "Touch: $TD · ROM: ${ROM:-(Spieleliste)}"
    (
        cd "$A" || exit 1
        export XDG_RUNTIME_DIR=/var/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1 SDL_VIDEODRIVER=wayland
        export LD_LIBRARY_PATH="$A/lib:/usr/lib:/lib" NNDDSS_TOUCH_DEV="$TD"
        [ -f /usr/config/SDL-GameControllerDB/gamecontrollerdb.txt ] && \
            export SDL_GAMECONTROLLERCONFIG_FILE=/usr/config/SDL-GameControllerDB/gamecontrollerdb.txt
        if [ -n "$ROM" ]; then exec ./nnddss.rds --rom "$ROM"; else exec ./nnddss.rds --roms /storage/roms/nds; fi
    ) > "$LOG" 2>&1 &
    for i in $(seq 1 40); do
        sleep 0.25
        swaymsg -t get_tree | grep -q '"app_id": "nnddss' && break
    done
    swaymsg -t get_tree | python3 -c 'import json,sys
def w(n):
    if str(n.get("app_id","")).startswith("nnddss") or "nnddss" in str((n.get("window_properties") or {}).get("class","")):
        print("Fenster:", n.get("app_id"), n["rect"], "fullscreen", n.get("fullscreen_mode"))
    for c in n.get("nodes",[])+n.get("floating_nodes",[]): w(c)
w(json.load(sys.stdin))'
    swaymsg '[app_id="^nnddss"] fullscreen enable global, focus' >/dev/null 2>&1
    sleep 1
    pidof nnddss.rds >/dev/null && echo "läuft (pid $(pidof nnddss.rds))" || { echo "beendet – Log:"; tail -30 "$LOG"; }
    ;;
stopp)
    pkill -TERM -f nnddss.rds; sleep 2; pkill -KILL -f nnddss.rds 2>/dev/null; echo "gestoppt"
    ;;
log)
    tail -60 "$LOG"
    ;;
entfernen)
    pkill -KILL -f nnddss.rds 2>/dev/null
    rm -rf "$A" /tmp/nnddss && echo "Entfernt: $A (Spielstände bleiben in $DATA)"
    ;;
*)
    sed -n '2,12p' "$0"
    ;;
esac
