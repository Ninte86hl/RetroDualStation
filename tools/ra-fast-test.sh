#!/bin/bash
# Schnellwechsel mit RetroArch ausprobieren – ohne das Kontrollcenter zu ändern.
# Aufruf auf dem Gerät (ES in der Systemansicht, kein Spiel offen):  bash /storage/ra-fast-test.sh
# Ablauf: 1) RetroArch-Spiel einmal über ES starten → Startbefehl merken → beenden
#         2) SM64 (DSperate) über ES starten → prüfen → einfrieren
#         3) RetroArch-Spiel mit dem gemerkten Befehl an ES vorbei starten → prüfen
#         4) RetroArch beenden → SM64 aufwecken (Touch-Zuordnung + Fokus) → prüfen
# Optional: RA="Teil des ROM-Namens" (Standard: Super Metroid), DS="Teil des DS-ROM-Namens" (Standard: Mario 64)
LOG=/storage/ra-fast-test.log
export XDG_RUNTIME_DIR=/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1 SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock
: > "$LOG"
say() { echo "$(date +%H:%M:%S) $*" | tee -a "$LOG"; }
frage() { local g="$2"
    read -r -p "  Gehen die TASTEN in $g? (j/n) " K
    read -r -p "  Geht der TOUCH bzw. stimmt das BILD in $g? (j/n) " A
    say "$1: Tasten $K · Touch/Bild $A"; }
mem() { free -m | awk '/Mem:/{printf "%s MB frei", $7} /Swap:/{printf " · zram belegt %s MB", $3}'; }
desc() { local p=$1; for c in $(pgrep -P "$p"); do echo "$c"; desc "$c"; done; }
fenster() { swaymsg -t get_tree | python3 -c '
import json,sys
def walk(n,out=None):
    if n.get("type")=="output": out=n["name"]
    if n.get("type") in ("con","floating_con") and n.get("pid"):
        r=n["rect"]; print("   %-12s %-28s out=%s fs=%s rect=%dx%d+%d+%d" % (n.get("app_id"),(n.get("name") or "")[:28],out,n.get("fullscreen_mode"),r["width"],r["height"],r["x"],r["y"]))
    for c in n.get("nodes",[])+n.get("floating_nodes",[]): walk(c,out)
walk(json.load(sys.stdin))' | tee -a "$LOG"; }
ROM_RA=$(find /storage/roms -type f -iname "*${RA:-Super Metroid}*" ! -path "*/nds/*" | head -1)
ROM_DS=$(ls /storage/roms/nds/*.nds | grep -i "${DS:-mario.*64}" | head -1)
[ -n "$ROM_RA" ] && [ -n "$ROM_DS" ] || { say "FEHLER: ROMs nicht gefunden"; exit 1; }
say "RetroArch-Spiel: $ROM_RA"
say "DS-Spiel: $ROM_DS · $(mem)"

# 1. RetroArch-Startbefehl über ES abschauen
curl -s -X POST --data-binary "$ROM_RA" http://127.0.0.1:1234/launch >/dev/null
for i in $(seq 1 120); do RAP=$(pidof retroarch) && break; sleep 0.25; done
[ -n "$RAP" ] || { say "FEHLER: RetroArch startet nicht"; exit 1; }
sleep 4
RU=$(pgrep -x runemu.sh | head -1)
mapfile -d '' RA_ARGS < /proc/$RU/cmdline
say "RetroArch über ES: $(awk '/VmRSS/{print int($2/1024)" MB"}' /proc/$RAP/status) · $(mem)"
say "Startbefehl: ${RA_ARGS[*]}"
kill -TERM $RAP; for i in $(seq 1 40); do pidof retroarch >/dev/null || break; sleep 0.25; done
sleep 4

# 2. DS-Spiel über ES (Anker)
say "Starte das DS-Spiel über ES …"
curl -s -X POST --data-binary "$ROM_DS" http://127.0.0.1:1234/launch >/dev/null
for i in $(seq 1 120); do EMU=$(pidof dsperate || pidof drastic) && break; sleep 0.25; done
[ -n "$EMU" ] || { say "FEHLER: DS-Emulator startet nicht"; exit 1; }
sleep 6
RU=$(pgrep -x runemu.sh | head -1)
EMUNAME=$(cat /proc/$EMU/comm)
say "1/3 DS-Spiel läuft ($EMUNAME) – bitte prüfen:"
frage "Vorher DS" "$EMUNAME"
PIDS=$(desc $RU | tr '\n' ' ')
kill -STOP $PIDS
say "DS-Spiel eingefroren ($PIDS) · $(mem)"

# 3. RetroArch an ES vorbei, Umgebung und Ordner vom Anker
CWD=$(readlink /proc/$RU/cwd)
mapfile -d '' ENVS < /proc/$RU/environ
T0=$(date +%s%N)
( cd "$CWD" && env -i "${ENVS[@]}" setsid "${RA_ARGS[@]}" >/dev/null 2>&1 & )
for i in $(seq 1 120); do RAP=$(pidof retroarch) && break; sleep 0.25; done
for i in $(seq 1 60); do swaymsg -t get_tree | grep -q '"app_id": "retroarch"' && break; sleep 0.25; done
say "RetroArch-Fenster nach $(( ($(date +%s%N) - T0) / 1000000 )) ms · $(mem)"
sleep 3
say "Fenster:"; fenster
say "2/3 RetroArch läuft – bitte prüfen (Bild auf dem richtigen Bildschirm?):"
frage "Während RetroArch" "RetroArch"
say "Speicher mit beiden Spielen: $(mem)"

# 4. RetroArch beenden, Anker zurück
kill -TERM $(pidof retroarch); for i in $(seq 1 40); do pidof retroarch >/dev/null || break; sleep 0.25; done
pkill -KILL retroarch 2>/dev/null
T0=$(date +%s%N)
swaymsg 'input type:touch map_to_output *' >/dev/null
kill -CONT $PIDS
swaymsg "[pid=$EMU title=Bottom] focus" >/dev/null 2>&1
say "DS-Spiel aufgeweckt nach $(( ($(date +%s%N) - T0) / 1000000 )) ms · $(mem)"
sleep 2
say "Fenster:"; fenster
say "3/3 DS-Spiel zurück – bitte prüfen (ganzer unterer Bildschirm):"
frage "Nachher DS" "$EMUNAME"
kill -TERM $EMU
say "Fertig – zurück in ES"
