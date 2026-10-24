#!/bin/bash
# Ursache suchen: Warum verliert DSperate den Touch, nachdem DraStic lief?
# Aufruf auf dem Gerät (ES in der Systemansicht, kein Spiel offen):  bash /storage/drastic-touch-test.sh <a|b|c|d>
#   a = DraStic über start_drastic.sh (mit gptokeyb und libdrastouch), ohne runemu
#   b = DraStic über runemu.sh – genau wie der Schnellwechsel
#   c = DraStic nackt: ohne gptokeyb, ohne libdrastouch
#   d = DraStic mit libdrastouch, aber ohne gptokeyb
#   e = Gegenprobe: RetroArch (nur Menü) statt DraStic, ebenfalls global im Vollbild
#   f = Gegenprobe: wie e, aber RetroArch nur auf dem oberen Bildschirm (kein globales Vollbild)
# Zusatz: MAP=1 ordnet den Touchscreen nach dem DraStic-Start und nach dem Aufwecken fest dem unteren Bildschirm zu
#         (UNTEN=<Ausgang>, Standard DSI-1) und setzt den Fokus aufs untere DSperate-Fenster.
#         MAP=2 lädt nach dem Aufwecken stattdessen die Sway-Konfiguration neu (wie es ES bei jedem Start tut).
# Ablauf: SM64 über ES starten → einfrieren → DraStic (Zelda) 15 s → DraStic beenden → SM64 aufwecken → Touch prüfen.
V="${1:-a}"
LOG=/storage/drastic-touch-test.log
export XDG_RUNTIME_DIR=/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1 SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock
say() { echo "$(date +%H:%M:%S) [$V] $*" | tee -a "$LOG"; }
frage() {   # $1 = Bezeichnung, $2 = Spiel (Standard SM64); setzt A = Touch-Antwort
    local g="${2:-SM64}"
    read -r -p "  Gehen die TASTEN in $g? (j/n) " K
    read -r -p "  Geht der TOUCH in $g? (j/n) " A
    say "$1: Tasten $K · Touch $A"
}
ROM_A=$(ls /storage/roms/nds/*.nds | grep -i "mario.*64" | head -1)
ROM_B=$(ls /storage/roms/nds/*.nds | grep -i "zelda.*phantom" | head -1)

T0=$(date +%s)
say "Start SM64 über ES"
curl -s -X POST --data-binary "$ROM_A" http://127.0.0.1:1234/launch >/dev/null
sleep 12
DSP=$(pidof dsperate); RU=$(pgrep -f "runemu.sh.*Mario" | head -1)
[ -n "$DSP" ] || { say "FEHLER: DSperate läuft nicht"; exit 1; }
say "1/3 SM64 läuft – bitte prüfen:"
frage "Vorher SM64"
holders() { for p in /proc/[0-9]*; do ls -l $p/fd 2>/dev/null | grep -q "/dev/input/event1$" && echo "$(basename $p) $(cat $p/comm)"; done | tr '\n' ' '; }
snap() { { swaymsg -t get_seats; swaymsg -t get_inputs; ps -o pid,args | grep -iE "[x]wayland|[g]ptokeyb|[d]rastic"; } > "/storage/dtt-$1.txt" 2>&1; }
snap vorher
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
  e|f) ( retroarch >/dev/null 2>&1 & ) ;;
esac
for i in $(seq 1 40); do swaymsg -t get_tree | grep -qE '"app_id": "(drastic|retroarch)"' && break; sleep 0.25; done
sleep 1
case "$V" in
  e) swaymsg "[pid=$(pidof retroarch)] fullscreen enable global, focus" >/dev/null 2>&1 ;;
  f) swaymsg "[pid=$(pidof retroarch)] move to output DSI-2, fullscreen enable, focus" >/dev/null 2>&1 ;;
  *) if [ "$NOGLOBAL" = 1 ]; then say "ohne globales Vollbild"; else
       swaymsg "[pid=$(pidof drastic)] fullscreen enable global, focus" >/dev/null 2>&1; fi ;;   # wie beim Schnellwechsel
esac
if [ "$MAP" = 1 ]; then swaymsg "input type:touch map_to_output ${UNTEN:-DSI-1}" >/dev/null; say "Touch fest auf ${UNTEN:-DSI-1} (während DraStic)"; fi
say "Fenster: $(swaymsg -t get_tree | grep -oE '"(app_id|shell|name)": "[^"]*"' | grep -iE -A2 -B1 'drastic|retroarch' | tr '\n' ' ' | head -c 300)"
snap waehrend
say "Touchscreen (event1) offen bei: $(holders)"
say "2/3 Zelda läuft – bitte prüfen:"
frage "Während Zelda" "Zelda"
for p in $(pidof drastic) $(pidof retroarch); do kill -TERM "$p"; done
for i in 1 2 3 4 5 6 7 8 9 10; do pidof drastic retroarch >/dev/null || break; sleep 0.3; done
for p in $(pidof drastic) $(pidof retroarch) $(pidof gptokeyb); do kill -KILL "$p" 2>/dev/null; done
sleep 0.5
if pidof drastic >/dev/null; then say "WARNUNG: DraStic läuft noch (PID $(pidof drastic))"; else say "DraStic beendet"; fi
sleep 1
kill -CONT $DSP
if [ "$MAP" = 2 ]; then
    sleep 0.5
    swaymsg reload >/dev/null
    sleep 1
    swaymsg "[pid=$DSP title=Bottom] focus" >/dev/null 2>&1
    say "Sway-Konfiguration neu geladen (wie beim ES-Start), Fokus aufs untere DSperate-Fenster"
fi
if [ "$MAP" = 1 ]; then
    sleep 0.5
    swaymsg "input type:touch map_to_output ${UNTEN:-DSI-1}" >/dev/null
    swaymsg "[pid=$DSP title=Bottom] focus" >/dev/null 2>&1
    say "Touch fest auf ${UNTEN:-DSI-1}, Fokus aufs untere DSperate-Fenster"
fi
say "3/3 SM64 aufgeweckt – gleich prüfen"
snap nachher
say "Touchscreen (event1) offen bei: $(holders)"
sleep 1
say "DSperate: $(grep -E '^State' /proc/$DSP/status 2>/dev/null || echo 'Prozess weg!') · Threads $(ls /proc/$DSP/task 2>/dev/null | wc -l) · Fenster $(swaymsg -t get_tree | grep -c '"app_id": "dsperate"')"
say "Meldungen von DSperate/Wayland seit dem Start:"
journalctl --since "@$T0" --no-pager 2>/dev/null | grep -iE "dsperate|wayland|broken pipe|display|wl_|disconnect|EPIPE|error" | grep -v rds-cc | tail -12 | tee -a "$LOG"
say "Unterschiede vorher/nachher:"; diff /storage/dtt-vorher.txt /storage/dtt-nachher.txt | grep -vE '"(id|pid)"' | head -30 | tee -a "$LOG"
frage "Ergebnis nach DraStic"
if [ "$A" = n ] && [ "$REPAIR" = 1 ]; then
    seats() { swaymsg -t get_seats | grep -E '"name": "seat|"focus"' | tr -d ' \n'; }
    say "Reparatur 1: Fokus auf das untere DSperate-Fenster · Seats vorher: $(seats)"
    swaymsg "[app_id=dsperate title=Bottom] focus" >/dev/null
    say "  Seats nachher: $(seats)"
    frage "  Ergebnis Reparatur 1"
    if [ "$A" = n ]; then
        say "Reparatur 2: Zeiger-Sperre lösen (pointer_constraint escape) auf beiden Seats"
        for st in seat0 seat1; do swaymsg "seat $st pointer_constraint escape" >/dev/null 2>&1; done
        frage "  Ergebnis Reparatur 2"
        if [ "$A" = n ]; then
            say "Reparatur 3: Touchscreen in Sway neu anmelden (Gerät kurz trennen)"
            dev=$(basename "$(readlink -f /sys/class/input/event1/device/device)")
            drv=$(basename "$(readlink -f /sys/class/input/event1/device/device/driver)")
            echo "$dev" > /sys/bus/i2c/drivers/$drv/unbind 2>/dev/null; sleep 1
            echo "$dev" > /sys/bus/i2c/drivers/$drv/bind 2>/dev/null; sleep 2
            say "  Treiber $drv / $dev neu gebunden"
            frage "  Ergebnis Reparatur 3"
        fi
    fi
fi
kill -TERM $DSP
say "SM64 beendet – zurück in ES"
