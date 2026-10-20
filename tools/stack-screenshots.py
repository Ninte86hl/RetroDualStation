#!/usr/bin/env python3
"""Dual-Screen-Screenshots übereinander anordnen (wie am Gerät).

grim nimmt beide Bildschirme nebeneinander auf (links oben, rechts unten,
2048 x 768). Dieses Werkzeug legt den oberen über den unteren Bildschirm mit
einem schmalen Spalt (Scharnier). Bereits umgewandelte Bilder (höher als breit)
werden übersprungen.

Aufruf:
    python3 tools/stack-screenshots.py docs/screenshots/*.png
"""
import sys
from PIL import Image

GAP = 24              # Abstand zwischen den Bildschirmen (Scharnier)
GAP_COLOR = (24, 24, 24)

for path in sys.argv[1:]:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if h >= w or w != 2 * h * 4 // 3:      # nur 2 x 4:3 nebeneinander
        print("übersprungen:", path, im.size)
        continue
    half = w // 2
    top, bottom = im.crop((0, 0, half, h)), im.crop((half, 0, w, h))
    out = Image.new("RGB", (half, 2 * h + GAP), GAP_COLOR)
    out.paste(top, (0, 0))
    out.paste(bottom, (0, h + GAP))
    out.save(path, optimize=True)
    print("umgewandelt:", path, out.size)
