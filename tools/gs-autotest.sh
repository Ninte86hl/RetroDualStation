#!/bin/bash
# Automatischer Gameswitcher-Test auf dem Gerät:  bash /storage/gs-autotest.sh [umgekehrt]
# Startet Spiel A über ES, wechselt per Gameswitcher zu B, zurück zu A, beendet – je ~10 s Spielzeit.
# Standard: A = Super Mario 64 DS (DSperate), B = Zelda Phantom Hourglass (DraStic). "umgekehrt" tauscht A und B.
# Beide Spiele müssen schon im Gameswitcher stehen (einmal gespielt). Ergebnis: /storage/gs-autotest.log
A="Mario 64"; B="Zelda"
[ "$1" = "umgekehrt" ] && { A="Zelda"; B="Mario 64"; }
[ -n "$2" ] && { A="$1"; B="$2"; }          # eigene Spiele: bash gs-autotest.sh "Mario 64" "Metroid"
LOG=/storage/gs-autotest.log
ROM_A=$(ls /storage/roms/*/* 2>/dev/null | grep -i "${A// /.*}" | grep -viE "\.(png|jpg|xml|txt)$" | head -1)
[ -n "$ROM_A" ] || { echo "Spiel nicht gefunden: $A"; exit 1; }
T0=$(date +%s)
say() { echo "$(date +%H:%M:%S) $*"; }
step() { say "$1"; echo "$2" > /tmp/rds-gs-test; }

say "Start über ES: $(basename "$ROM_A")"
curl -s -X POST --data-binary "$ROM_A" http://127.0.0.1:1234/launch >/dev/null
sleep 14
step "Wechsel zu $B" "$B";  sleep 16
step "Zurück zu $A" "$A";   sleep 12
step "Beenden" "quit";      sleep 6
say "fertig"
[ "$KEEP" = 1 ] || true
{ echo "=== Gameswitcher-Test $A ⇄ $B ==="
  journalctl -u rds-controlcenter --since "@$T0" --no-pager | grep -E "Test:|Schnellwechsel|Gameswitcher|Spiel beenden|Fehler|Traceback|Error" | sed 's/^.*\[rds-cc\] //'
  free -m | head -2; } > "$LOG"
cat "$LOG"
