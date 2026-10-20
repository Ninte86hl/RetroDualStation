#!/bin/bash
# Screenshot vom Gerät holen und gleich übereinander anordnen.
# Aufruf: tools/screenshot.sh <name> [IP]   → docs/screenshots/<name>.png
NAME="${1:?Name angeben, z. B. control-center-main}"
IP="${2:-192.168.178.80}"
DIR="$(cd "$(dirname "$0")/.." && pwd)/docs/screenshots"
ssh root@"$IP" "WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR=/run/0-runtime-dir grim /tmp/rds-shot.png" &&
scp -q root@"$IP":/tmp/rds-shot.png "$DIR/$NAME.png" &&
python3 "$(dirname "$0")/stack-screenshots.py" "$DIR/$NAME.png"
