import math, sys
from PIL import Image, ImageDraw, ImageFont

S = 2
W, H = 1024 * S, 768 * S
F = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
def font(sz, w="Regular"):
    return ImageFont.truetype(F % w, int(sz * S))

BG, CARD, TILE, TEXT, MUTED = (55, 55, 55), (38, 38, 38), (74, 74, 74), (255, 255, 255), (189, 189, 189)
RED, BLUE, GREEN, YEL, PURP, ORANGE = (229, 56, 59), (64, 124, 255), (45, 182, 122), (245, 190, 30), (155, 93, 229), (240, 128, 48)

CATS = [("Anzeige", BLUE, "display"), ("Spiele", GREEN, "game"), ("Controller", PURP, "pad"),
        ("Netzwerk", ORANGE, "wifi"), ("System", YEL, "gear"), ("RDS", RED, "rds")]
SEL = 0

def s(v): return int(v * S)

def icon(d, kind, cx, cy, r, col, lw):
    w = s(lw)
    if kind == "display":
        d.rounded_rectangle((cx - r, cy - r * 0.95, cx + r, cy - r * 0.05), radius=s(4) * r / s(30), outline=col, width=w)
        d.rounded_rectangle((cx - r, cy + r * 0.05, cx + r, cy + r * 0.95), radius=s(4) * r / s(30), outline=col, width=w)
    elif kind == "game":
        d.rounded_rectangle((cx - r, cy - r * 0.6, cx + r, cy + r * 0.6), radius=r * 0.5, outline=col, width=w)
        d.line((cx - r * 0.55, cy, cx - r * 0.15, cy), fill=col, width=w)
        d.line((cx - r * 0.35, cy - r * 0.2, cx - r * 0.35, cy + r * 0.2), fill=col, width=w)
        for dx, dy in ((0.4, -0.12), (0.6, 0.12)):
            rr = r * 0.09
            d.ellipse((cx + r * dx - rr, cy + r * dy - rr, cx + r * dx + rr, cy + r * dy + rr), fill=col)
    elif kind == "pad":
        for dx in (-0.45, 0.45):
            rr = r * 0.32
            d.ellipse((cx + r * dx - rr, cy - rr, cx + r * dx + rr, cy + rr), outline=col, width=w)
        d.line((cx - r * 0.45, cy - r * 0.32, cx - r * 0.45, cy - r * 0.8), fill=col, width=w)
        d.line((cx + r * 0.45, cy - r * 0.32, cx + r * 0.45, cy - r * 0.8), fill=col, width=w)
    elif kind == "wifi":
        for k in (1.0, 0.68, 0.36):
            d.arc((cx - r * k, cy - r * k + r * 0.4, cx + r * k, cy + r * k + r * 0.4), 225, 315, fill=col, width=w)
        rr = r * 0.1
        d.ellipse((cx - rr, cy + r * 0.4 - rr, cx + rr, cy + r * 0.4 + rr), fill=col)
    elif kind == "gear":
        for i in range(8):
            a = i * math.pi / 4
            d.line((cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55, cx + math.cos(a) * r * 0.95, cy + math.sin(a) * r * 0.95), fill=col, width=int(w * 1.8))
        d.ellipse((cx - r * 0.65, cy - r * 0.65, cx + r * 0.65, cy + r * 0.65), outline=col, width=w)
        d.ellipse((cx - r * 0.25, cy - r * 0.25, cx + r * 0.25, cy + r * 0.25), outline=col, width=w)
    elif kind == "rds":
        d.rounded_rectangle((cx - r * 0.7, cy - r * 0.95, cx + r * 0.7, cy - r * 0.08), radius=r * 0.12, outline=TEXT, width=w)
        d.rounded_rectangle((cx - r * 0.7, cy + r * 0.08, cx + r * 0.7, cy + r * 0.95), radius=r * 0.12, outline=col, width=w)

def toggle(d, x, y, on, col):
    d.rounded_rectangle((x, y, x + s(58), y + s(32)), radius=s(16), fill=col if on else TILE)
    cx = x + (s(42) if on else s(16))
    d.ellipse((cx - s(12), y + s(4), cx + s(12), y + s(28)), fill=TEXT)

# ---------- unterer Bildschirm ----------
bot = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(bot)
d.text((s(40), s(26)), "23:41", font=font(40, "SemiBold"), fill=TEXT)
d.text((s(512), s(46)), "Einstellungen", font=font(30, "SemiBold"), fill=TEXT, anchor="mm")
d.rounded_rectangle((s(870), s(28), s(984), s(66)), radius=s(19), fill=CARD)
d.text((s(927), s(47)), "B  Zurück", font=font(15), fill=MUTED, anchor="mm")
# Karussell
cw, gap = 132, 18
x0 = 512 - (cw * 3 + gap * 2.5) - 4
for i, (name, col, kind) in enumerate(CATS):
    big = i == SEL
    x = s(40 + i * (cw + 25)); y = s(92)
    size = s(cw)
    d.rounded_rectangle((x, y, x + size, y + s(128)), radius=s(22), fill=CARD, outline=col if big else None, width=s(4) if big else 0)
    icon(d, kind, x + size / 2, y + s(52), s(28), col, 5)
    d.line((x + s(22), y + s(104), x + size - s(22), y + s(104)), fill=col, width=s(4))
    d.text((x + size / 2, y + s(150)), name, font=font(18, "SemiBold" if big else "Regular"), fill=TEXT if big else MUTED, anchor="mm")
# Liste
d.rounded_rectangle((s(40), s(262), s(984), s(700)), radius=s(24), fill=CARD)
rows = [("Theme (Dual-Screen)", "canvas rds", None, BLUE),
        ("Theme (Single-Screen)", "System-Theme", None, BLUE),
        ("Ansicht der Spieleliste", "Raster 3×1", None, BLUE),
        ("Hell / Dunkel", None, True, BLUE),
        ("Bildschirmschoner", "Dimmen · 5 min", None, BLUE),
        ("Unteren Bildschirm abdunkeln (RetroArch)", None, True, BLUE)]
for i, (lbl, val, tog, col) in enumerate(rows):
    y = s(278 + i * 70)
    if i == 0:
        d.rounded_rectangle((s(52), y, s(972), y + s(60)), radius=s(14), fill=TILE)
    d.text((s(76), y + s(30)), lbl, font=font(21, "Medium"), fill=TEXT, anchor="lm")
    if tog is not None:
        toggle(d, s(890), y + s(14), tog, col)
    else:
        d.text((s(912), y + s(30)), val, font=font(19), fill=MUTED, anchor="rm")
        d.text((s(948), y + s(30)), "›", font=font(28), fill=MUTED, anchor="mm")
d.text((s(40), s(735)), "L1 / R1  Kategorie", font=font(16), fill=MUTED, anchor="lm")
for i in range(len(CATS)):
    cx = s(512 - (len(CATS) - 1) * 9 + i * 18)
    if i == SEL:
        d.rounded_rectangle((cx - s(12), s(731), cx + s(12), s(739)), radius=s(4), fill=TEXT)
    else:
        d.ellipse((cx - s(4), s(731), cx + s(4), s(739)), fill=(110, 110, 110))
d.text((s(984), s(735)), "A  Auswählen", font=font(16), fill=MUTED, anchor="rm")

# ---------- oberer Bildschirm ----------
top = Image.new("RGB", (W, H), BG); t = ImageDraw.Draw(top)
t.text((s(984), s(40)), "Anzeige", font=font(18), fill=MUTED, anchor="rm")
# 1:1-Bild zur Kategorie
bx, by, bs = s(60), s(150), s(420)
t.rounded_rectangle((bx, by, bx + bs, by + bs), radius=s(36), fill=CARD)
icon(t, "display", bx + bs / 2, by + bs / 2 - s(20), s(120), BLUE, 12)
t.line((bx + s(60), by + bs - s(50), bx + bs - s(60), by + bs - s(50)), fill=BLUE, width=s(8))
# Text
tx = s(530)
t.text((tx, s(170)), "Theme (Dual-Screen)", font=font(38, "SemiBold"), fill=TEXT)
t.rounded_rectangle((tx, s(232), tx + s(150), s(268)), radius=s(18), fill=BLUE)
t.text((tx + s(75), s(250)), "canvas rds", font=font(17, "SemiBold"), fill=TEXT, anchor="mm")
desc = ["Das Aussehen von EmulationStation, wenn",
        "RDS beide Bildschirme nutzt.",
        "",
        "canvas rds zeigt oben Hero-Bild und Video,",
        "unten die Spieleliste in fünf Ansichten.",
        "dii-ess-aye rds ist schlichter und schneller.",
        "",
        "Dein Single-Screen-Theme bleibt davon",
        "unberührt."]
for i, ln in enumerate(desc):
    t.text((tx, s(300 + i * 34)), ln, font=font(21), fill=MUTED if ln else TEXT)
t.text((s(512), s(720)), "Änderungen gelten sofort  ·  gespeichert in der ROCKNIX-Konfiguration", font=font(16), fill=(140, 140, 140), anchor="mm")

out = Image.new("RGB", (1024, 768 * 2 + 24), (0, 0, 0))
out.paste(top.resize((1024, 768), Image.LANCZOS), (0, 0))
out.paste(bot.resize((1024, 768), Image.LANCZOS), (0, 792))
out.save(sys.argv[1])
