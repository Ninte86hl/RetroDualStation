#!/bin/bash
# Ursache suchen: Warum verliert DSperate den Touch, nachdem DraStic lief?
# Aufruf auf dem Gerät (ES in der Systemansicht, kein Spiel offen):  bash /storage/drastic-touch-test.sh <a|b|c|d>
#   a = DraStic über start_drastic.sh (mit gptokeyb und libdrastouch), ohne runemu
#   b = DraStic über runemu.sh – genau wie der Schnellwechsel
#   c = DraStic nackt: ohne gptokeyb, ohne libdrastouch
#   d = DraStic mit libdrastouch, aber ohne gptokeyb
# Ablauf: SM64 über ES starten → einfrieren → DraStic (Zelda) 15 s → DraStic beenden → SM64 aufwecken → Touch prüfen.
V="${1:-a}"
LOG=/storage/drastic-touch-test.log
export XDG_RUNTIME_DIR=/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1 SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock
say() { echo "$(date +%H:%M:%S) [$V] $*" | tee -a "$LOG"; }
ROM_A=$(ls /storage/roms/nds/*.nds | grep -i "mario.*64" | head -1)
ROM_B=$(ls /storage/roms/nds/*.nds | grep -i "zelda.*phantom" | head -1)

say "Start SM64 über ES"
curl -s -X POST --data-binary "$ROM_A" http://127.0.0.1:1234/launch >/dev/null
sleep 12
DSP=$(pidof dsperate); RU=$(pgrep -f "runemu.sh.*Mario" | head -1)
[ -n "$DSP" ] || { say "FEHLER: DSperate läuft nicht"; exit 1; }
say "Touch in SM64 JETZT kurz prüfen (5 s) …"; sleep 5
kill -STOP $DSP; say "SM64 eingefroren"

case "$V" in
  a) /usr/bin/start_drastic.sh "$ROM_B" >/dev/null 2>&1 & ;;
  b) mapfile -d '' ARGS < /proc/$RU/cmdline
     NEW=(); for x in "${ARGS[@]}"; do
       case "$x" in "$ROM_A") x="$ROM_B";; --emulator=*) x="--emulator=drastic";; --core=*) x="--core=drastic-sa";; esac
       NEW+=("$x"); done
     ( cd "$(readlink /proc/$RU/cwd)"; setsid "${NEW[@]}" >/dev/null 2>&1 & ) ;;
  c) ( cd /storage/.config/drastic && SDL_TOUCH_MOUSE_EVENTS=0 ./drastic "$ROM_B" >/dev/null 2>&1 & ) ;;
  d) ( cd /storage/.config/drastic && LD_PRELOAD=/usr/lib/libdrastouch.so SDL_TOUCH_MOUSE_EVENTS=0 ./drastic "$ROM_B" >/dev/null 2>&1 & ) ;;
esac
sleep 3
swaymsg "[pid=$(pidof drastic)] fullscreen enable global, focus" >/dev/null 2>&1   # wie beim Schnellwechsel: über beide Bildschirme
say "DraStic gestartet – 12 s (Touch in Zelda darf benutzt werden)"
sleep 12
for p in $(pidof drastic); do kill -TERM "$p"; done
for i in 1 2 3 4 5 6 7 8 9 10; do pidof drastic >/dev/null || break; sleep 0.3; done
for p in $(pidof drastic) $(pidof gptokeyb); do kill -KILL "$p" 2>/dev/null; done
sleep 0.5
if pidof drastic >/dev/null; then say "WARNUNG: DraStic läuft noch (PID $(pidof drastic))"; else say "DraStic beendet"; fi
sleep 1
kill -CONT $DSP
say "SM64 aufgeweckt – jetzt Touch prüfen!"
read -r -p "Geht der Touch in SM64? (j/n) " A
say "Ergebnis Touch nach DraStic: $A"
kill -TERM $DSP
say "SM64 beendet – zurück in ES"
