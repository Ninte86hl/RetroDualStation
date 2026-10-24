#!/bin/bash
# DSperate von innen: Wayland-Verkehr protokollieren, um zu sehen, warum der Touch nach DraStic fehlt.
# Aufruf auf dem Gerät (ES in der Systemansicht):  bash /storage/dsperate-wayland-test.sh
# Ablauf: Hülle mit WAYLAND_DEBUG über /usr/bin/dsperate legen → SM64 über ES starten
#         → prüfen → einfrieren → DraStic (Zelda) → beenden → SM64 aufwecken → prüfen → Auswertung.
LOG=/storage/dsperate-wayland-test.log
WL=/storage/dsp-wl.log
export XDG_RUNTIME_DIR=/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1 SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock
: > "$LOG"
say() { echo "$(date +%H:%M:%S) $*" | tee -a "$LOG"; }
mark() { echo "=== RDS-MARKE $* ===" >> "$WL"; }
frage() { local g="${2:-SM64}"
    read -r -p "  Gehen die TASTEN in $g? (j/n) " K
    read -r -p "  Geht der TOUCH in $g? (j/n) " A
    say "$1: Tasten $K · Touch $A"; }
ROM_A=$(ls /storage/roms/nds/*.nds | grep -i "mario.*64" | head -1)
ROM_B=$(ls /storage/roms/nds/*.nds | grep -i "zelda.*phantom" | head -1)

# 1. Hülle über DSperate legen (nur bis zum Ende des Tests), dann SM64 ganz normal über ES starten
: > "$WL"
cp /usr/bin/dsperate /storage/.dsp-real
printf '#!/bin/sh\nWAYLAND_DEBUG=1 exec -a /usr/bin/dsperate /storage/.dsp-real "$@" 2>>%s\n' "$WL" > /storage/.dsp-wrap
chmod +x /storage/.dsp-real /storage/.dsp-wrap
mount --bind /storage/.dsp-wrap /usr/bin/dsperate || { say "FEHLER: Hülle ließ sich nicht einhängen"; exit 1; }
aufraeumen() { umount /usr/bin/dsperate 2>/dev/null; rm -f /storage/.dsp-real /storage/.dsp-wrap; }
trap aufraeumen EXIT
say "SM64 über ES starten (mit Wayland-Protokoll) …"
curl -s -X POST --data-binary "$ROM_A" http://127.0.0.1:1234/launch >/dev/null
for i in $(seq 1 80); do DSP=$(pgrep -o -x .dsp-real) && break; sleep 0.25; done
[ -n "$DSP" ] || { say "FEHLER: DSperate startet nicht"; exit 1; }
sleep 10
say "1/3 SM64 läuft – bitte prüfen (ruhig ein paar Mal unten tippen):"
mark "VORHER-Pruefung"
frage "Vorher SM64"

# 3. Einfrieren, DraStic
mark "EINFRIEREN"
kill -STOP $DSP; say "SM64 eingefroren"
( cd /storage/.config/drastic && SDL_TOUCH_MOUSE_EVENTS=0 ./drastic "$ROM_B" >/dev/null 2>&1 & )
for i in $(seq 1 40); do swaymsg -t get_tree | grep -q '"app_id": "drastic"' && break; sleep 0.25; done
sleep 1
swaymsg "[app_id=drastic] fullscreen enable global, focus" >/dev/null 2>&1
say "2/3 Zelda läuft – bitte prüfen:"
frage "Während Zelda" "Zelda"
for p in $(pidof drastic); do kill -TERM "$p"; done
for i in $(seq 1 10); do pidof drastic >/dev/null || break; sleep 0.3; done
for p in $(pidof drastic); do kill -KILL "$p" 2>/dev/null; done
say "DraStic beendet"
sleep 1

# 4. Aufwecken
mark "AUFWECKEN"
kill -CONT $DSP
sleep 2
say "3/3 SM64 aufgeweckt – bitte prüfen (ruhig ein paar Mal unten tippen):"
mark "NACHHER-Pruefung"
frage "Nachher SM64"
fenster() { swaymsg -t get_tree | python3 -c '
import json,sys
def walk(n,out=None):
    if n.get("type")=="output": out=n["name"]
    if n.get("app_id") in ("dsperate","drastic"):
        r=n["rect"]; print("   %s %-22s out=%s fs=%s rect=%dx%d+%d+%d id=%s" % (n["app_id"],n.get("name"),out,n.get("fullscreen_mode"),r["width"],r["height"],r["x"],r["y"],n["id"]))
    for c in n.get("nodes",[])+n.get("floating_nodes",[]): walk(c,out)
walk(json.load(sys.stdin))' | tee -a "$LOG"; }
say "Fenster nach dem Aufwecken:"; fenster
if [ "$A" = n ]; then
    say "Reparatur: Vollbild beider DSperate-Fenster neu setzen, Fokus aufs untere"
    for id in $(swaymsg -t get_tree | python3 -c '
import json,sys
def walk(n):
    if n.get("app_id")=="dsperate": print(n["id"])
    for c in n.get("nodes",[])+n.get("floating_nodes",[]): walk(c)
walk(json.load(sys.stdin))'); do
        swaymsg "[con_id=$id] fullscreen disable" >/dev/null; swaymsg "[con_id=$id] fullscreen enable" >/dev/null
    done
    swaymsg "[app_id=dsperate title=Bottom] focus" >/dev/null 2>&1
    sleep 1; fenster
    mark "REPARATUR"
    frage "Nach Reparatur"
fi
mark "ENDE"
kill -TERM $DSP

# 5. Auswertung: was kommt bei DSperate an?
say "=== Auswertung (Zeilen je Abschnitt) ==="
awk '
  /=== RDS-MARKE/ { sec=$3; next }
  { if (sec=="") sec="START" }
  /wl_touch[#@][0-9]+\.down/          { t[sec]++; match($0,/wl_surface#[0-9]+/); ziel[sec]=ziel[sec] " " substr($0,RSTART,RLENGTH) }
  /wl_touch[#@][0-9]+\.(cancel)/      { c[sec]++ }
  /wl_pointer[#@][0-9]+\.button/      { p[sec]++ }
  /xdg_toplevel[#@][0-9]+\.configure/ { cf[sec]++; last[sec]=$0 }
  /wl_seat@[0-9]+\.capabilities/   { cap[sec]=cap[sec] " " $0 }
  /wl_keyboard[#@][0-9]+\.(enter|leave)/ { } /wl_surface[#@][0-9]+\.(enter|leave)/ { el[sec]++ }
  /wl_keyboard[#@][0-9]+\.(enter|leave)/ { kb[sec]++ }
  END {
    n=split("START VORHER-Pruefung EINFRIEREN AUFWECKEN NACHHER-Pruefung REPARATUR", o, " ")
    for (i=1;i<=n;i++) { s=o[i]
      printf "%-17s touch-down %3d · touch-cancel %2d · maus-klick %3d · configure %3d · enter/leave %2d · tastatur-fokus %2d\n",
             s, t[s]+0, c[s]+0, p[s]+0, cf[s]+0, el[s]+0, kb[s]+0
      if (ziel[s] != "") print "    Touch ging an:" ziel[s]
      if (last[s] != "") print "    letzte configure: " substr(last[s], 1, 160)
    }
  }' "$WL" | tee -a "$LOG"
say "Diagnose: $(wc -l < "$WL") Zeilen · Schnittstellen: $(grep -oE '[a-z_0-9]+@[0-9]+\.[a-z_]+' "$WL" | sed 's/@[0-9]*//' | sort | uniq -c | sort -rn | head -12 | tr '\n' ' ')"
say "Seats im Protokoll: $(grep -oE 'wl_seat@[0-9]+\.name\("[^"]*"\)' "$WL" | sort -u | tr '\n' ' ')"
say "Protokoll: $WL ($(du -h "$WL" | cut -f1))"
