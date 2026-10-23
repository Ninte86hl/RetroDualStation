#!/bin/sh
# Bilderpflege: Kontrollcenter in allen Akzentfarben, dunkel und hell, als Screenshots.
# Aufruf auf dem PC:  sh tools/cc-shots.sh <IP> [Seite]
#   Seite: 0 = Schnelleinstellungen (Standard), 1 = Spiel, 2 = RetroAchievements …
# Ergebnis: docs/screenshots/cc-farben/cc-<modus>-<farbe>.png
# Voraussetzung: ES läuft, kein Spiel offen (Seite 0) – das CC wird selbst geöffnet.
IP="${1:?IP fehlt}"
PAGE="${2:-0}"
OUT="docs/screenshots/cc-farben"
mkdir -p "$OUT"
ssh root@"$IP" "PAGE=$PAGE sh -s" <<'REMOTE'
export XDG_RUNTIME_DIR=/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1
BOTTOM=DSI-1   # unterer Bildschirm auf RG DS und RG DS Plus
rm -rf /tmp/rds-shots && mkdir -p /tmp/rds-shots
# CC vorab öffnen: das erste Öffnen dauert länger als ein Farbwechsel (sonst zeigt Bild 1 noch ES)
echo "dark e5383b $PAGE" > /tmp/rds-shot
sleep 3
for mode in dark light; do
  for acc in e5383b 3d7bff 2bb673 f08c00 9b5de5 e64980; do
    echo "$mode $acc $PAGE" > /tmp/rds-shot
    sleep 1.5
    grim -o "$BOTTOM" "/tmp/rds-shots/cc-$mode-$acc.png"
  done
done
echo end > /tmp/rds-shot
ls /tmp/rds-shots
REMOTE
scp "root@$IP:/tmp/rds-shots/*.png" "$OUT/"
