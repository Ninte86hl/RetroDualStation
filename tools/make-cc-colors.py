#!/usr/bin/env python3
"""Bilderpflege: Übersicht des Kontrollcenters in allen Akzentfarben, dunkel und hell.

Aufruf (im Repo-Ordner, nach tools/cc-shots.sh):
    python3 tools/make-cc-colors.py
Ergebnis: docs/screenshots/cc-farben.png und .webp (zwei Reihen: dunkel, hell · sechs Farben)
"""
import os
from PIL import Image, ImageDraw

SRC = "docs/screenshots/cc-farben"
OUT = "docs/screenshots/cc-farben"
ACCENTS = ["e5383b", "3d7bff", "2bb673", "f08c00", "9b5de5", "e64980"]
TW = 400                       # Breite eines Bildes in der Übersicht
GAP, PAD, R = 18, 30, 18

shots = {(m, a): os.path.join(SRC, f"cc-{m}-{a}.png") for m in ("dark", "light") for a in ACCENTS}
missing = [p for p in shots.values() if not os.path.exists(p)]
if missing:
    raise SystemExit("Fehlt: " + ", ".join(missing))

first = Image.open(shots[("dark", ACCENTS[0])])
TH = round(TW * first.height / first.width)
W = PAD * 2 + len(ACCENTS) * TW + (len(ACCENTS) - 1) * GAP
H = PAD * 2 + 2 * TH + GAP
canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
mask = Image.new("L", (TW, TH), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, TW - 1, TH - 1), radius=R, fill=255)
for row, mode in enumerate(("dark", "light")):
    for col, acc in enumerate(ACCENTS):
        im = Image.open(shots[(mode, acc)]).convert("RGB").resize((TW, TH), Image.LANCZOS)
        canvas.paste(im, (PAD + col * (TW + GAP), PAD + row * (TH + GAP)), mask)
canvas.save(OUT + ".png")
canvas.save(OUT + ".webp", quality=88, method=6)
print("geschrieben:", OUT + ".png", OUT + ".webp", f"({W}×{H})")
