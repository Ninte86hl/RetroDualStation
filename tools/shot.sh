#!/bin/sh
# Bilderpflege: beide Bildschirme auf einmal fotografieren.
# Aufruf auf dem PC (im Repo-Ordner):  sh tools/shot.sh <IP> <name>
# Ergebnis in docs/shots/:
#   <name>-oben.png, <name>-unten.png  – einzeln
#   <name>.png                         – übereinander (oben, 24 px Abstand, unten) für tools/make-mockup.py
IP="${1:?IP fehlt}"
NAME="${2:?Name fehlt}"
OUT="docs/shots"
mkdir -p "$OUT"
ssh root@"$IP" 'export XDG_RUNTIME_DIR=/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1
grim -o DSI-2 /tmp/rds-oben.png && grim -o DSI-1 /tmp/rds-unten.png' || exit 1
scp -q "root@$IP:/tmp/rds-oben.png" "$OUT/$NAME-oben.png"
scp -q "root@$IP:/tmp/rds-unten.png" "$OUT/$NAME-unten.png"
python3 - "$OUT/$NAME" <<'PY'
import sys
from PIL import Image
b = sys.argv[1]
top, bot = Image.open(b + "-oben.png"), Image.open(b + "-unten.png")
out = Image.new("RGB", (max(top.width, bot.width), top.height + 24 + bot.height), (0, 0, 0))
out.paste(top, (0, 0)); out.paste(bot, (0, top.height + 24))
out.save(b + ".png")
print("gespeichert:", b + ".png", out.size)
PY
