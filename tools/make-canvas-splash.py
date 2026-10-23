#!/usr/bin/env python3
"""Ladebildschirme für canvas rds: oberer Bildschirm-Ausschnitt der canvas-ds-Hintergründe je Farbschema.

Aufruf (im Repo-Ordner):
    git clone --depth 1 https://github.com/toniremi/canvas-ds /tmp/canvas-ds
    python3 tools/make-canvas-splash.py /tmp/canvas-ds
Der Hintergrund liegt im Theme mit minSize 1.5 × 1 über beiden Bildschirmen – der obere zeigt das
linke Drittel (die 640 × 480 des Originals). Deckkraft und Grundfarbe wie in colors.xml.
Ergebnis: theme/canvas-rds-overlay/_inc/splash/<schema>.webp (1024 × 768), genutzt von splash.xml.
"""
import re, sys
from pathlib import Path
from PIL import Image

src = Path(sys.argv[1])
out = Path(__file__).resolve().parent.parent / "theme" / "canvas-rds-overlay" / "_inc" / "splash"
out.mkdir(parents=True, exist_ok=True)
colors = (src / "colors.xml").read_text()
for m in re.finditer(r'ifSubset="color-scheme:(\w+)">(.*?)</variables>', colors, re.S):
    name, block = m.groups()
    v = dict(re.findall(r"<(\w+)>\s*([0-9a-fA-F.]+)\s*<", block))
    im = Image.open(src / "wallpapers" / f"{name}.webp").convert("RGB")
    top = im.crop((0, 0, im.width // 3, im.height)).resize((1024, 768), Image.LANCZOS)
    top = Image.blend(Image.new("RGB", top.size, "#" + v["backgroundColor"][:6]), top,
                      float(v.get("backgroundArtOpacity", "1")))
    top.save(out / f"{name}.webp", quality=85, method=6)
    print(name)
im = Image.open(src / "wallpapers" / "custom.webp").convert("RGB")
im.crop((0, 0, im.width // 3, im.height)).resize((1024, 768), Image.LANCZOS).save(out / "custom.webp", quality=85, method=6)
