#!/bin/bash
# DSperate von innen: Wayland-Verkehr protokollieren, um zu sehen, warum der Touch nach DraStic fehlt.
# Aufruf auf dem Gerät (ES in der Systemansicht):  bash /storage/dsperate-wayland-test.sh
# Ablauf: SM64 einmal über ES starten (Startbefehl abschauen) → beenden → SM64 selbst mit WAYLAND_DEBUG starten
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

# 1. Startbefehl von DSperate abschauen
say "SM64 über ES starten, um den Startbefehl von DSperate abzuschauen …"
curl -s -X POST --data-binary "$ROM_A" http://127.0.0.1:1234/launch >/dev/null
for i in $(seq 1 60); do DSP=$(pidof dsperate) && break; sleep 0.25; done
[ -n "$DSP" ] || { say "FEHLER: DSperate startet nicht"; exit 1; }
sleep 2
CWD=$(readlink /proc/$DSP/cwd)
mapfile -d '' CMD < /proc/$DSP/cmdline
mapfile -d '' ENVS < /proc/$DSP/environ
kill -TERM $DSP; for i in $(seq 1 30); do pidof dsperate >/dev/null || break; sleep 0.2; done
say "Startbefehl: ${CMD[*]}"
sleep 4    # ES kommt zurück

# 2. DSperate selbst starten, mit Protokoll
: > "$WL"
say "SM64 mit Wayland-Protokoll starten …"
( cd "$CWD" && env -i "${ENVS[@]}" WAYLAND_DEBUG=1 "${CMD[@]}" 2>>"$WL" >/dev/null & )
for i in $(seq 1 60); do DSP=$(pidof dsperate) && break; sleep 0.25; done
for i in $(seq 1 40); do [ "$(swaymsg -t get_tree | grep -c '"app_id": "dsperate"')" -ge 2 ] && break; sleep 0.25; done
sleep 3
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
mark "ENDE"
kill -TERM $DSP

# 5. Auswertung: was kommt bei DSperate an?
say "=== Auswertung (Zeilen je Abschnitt) ==="
awk '
  /=== RDS-MARKE/ { sec=$3; next }
  { if (sec=="") sec="START" }
  /wl_touch@[0-9]+\.down/          { t[sec]++ }
  /wl_touch@[0-9]+\.(cancel)/      { c[sec]++ }
  /wl_pointer@[0-9]+\.button/      { p[sec]++ }
  /xdg_toplevel@[0-9]+\.configure/ { cf[sec]++; last[sec]=$0 }
  /wl_seat@[0-9]+\.capabilities/   { cap[sec]=cap[sec] " " $0 }
  /wl_surface@[0-9]+\.(enter|leave)/ { el[sec]++ }
  /wl_keyboard@[0-9]+\.(enter|leave)/ { kb[sec]++ }
  END {
    n=split("START VORHER-Pruefung EINFRIEREN AUFWECKEN NACHHER-Pruefung", o, " ")
    for (i=1;i<=n;i++) { s=o[i]
      printf "%-17s touch-down %3d · touch-cancel %2d · maus-klick %3d · configure %3d · enter/leave %2d · tastatur-fokus %2d\n",
             s, t[s]+0, c[s]+0, p[s]+0, cf[s]+0, el[s]+0, kb[s]+0
      if (last[s] != "") print "    letzte configure: " substr(last[s], 1, 160)
    }
  }' "$WL" | tee -a "$LOG"
say "Seats im Protokoll: $(grep -oE 'wl_seat@[0-9]+\.name\("[^"]*"\)' "$WL" | sort -u | tr '\n' ' ')"
say "Protokoll: $WL ($(du -h "$WL" | cut -f1))"
