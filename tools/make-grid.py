#!/usr/bin/env python3
"""Bilderpflege: Übersicht aus mehreren Aufnahmen (z. B. Theme-Schemata, Ansichten).

Aufruf (im Repo-Ordner):
    python3 tools/make-grid.py <ziel.png> <spalten> <bild1> <bild2> … [--labels "A,B,C"]
Jedes Bild wird gleich groß mit abgerundeten Ecken auf transparentem Grund angeordnet;
optional mit Beschriftung darunter. Zusätzlich wird eine .webp gespeichert.
"""
import sys
from PIL import Image, ImageDraw, ImageFont

args = sys.argv[1:]
labels = None
if "--labels" in args:
    i = args.index("--labels")
    labels = [s.strip() for s in args[i + 1].split(",")]
    args = args[:i] + args[i + 2:]
out, cols, files = args[0], int(args[1]), args[2:]
ims = [Image.open(f).convert("RGB") for f in files]
TW = 480
TH = round(TW * ims[0].height / ims[0].width)
GAP, PAD, R, LH = 22, 30, 18, (40 if labels else 0)
rows = (len(ims) + cols - 1) // cols
W = PAD * 2 + cols * TW + (cols - 1) * GAP
H = PAD * 2 + rows * (TH + LH) + (rows - 1) * GAP
c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
mask = Image.new("L", (TW, TH), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, TW - 1, TH - 1), radius=R, fill=255)
d = ImageDraw.Draw(c)
try:
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
except OSError:
    font = ImageFont.load_default()
for n, im in enumerate(ims):
    x = PAD + (n % cols) * (TW + GAP)
    y = PAD + (n // cols) * (TH + LH + GAP)
    c.paste(im.resize((TW, TH), Image.LANCZOS), (x, y), mask)
    if labels and n < len(labels):
        d.text((x + TW / 2, y + TH + 10), labels[n], fill=(140, 140, 140, 255), font=font, anchor="mt")
c.save(out)
c.save(out.rsplit(".", 1)[0] + ".webp", quality=88, method=6)
print("geschrieben:", out, f"({W}×{H})")
