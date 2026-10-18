#!/usr/bin/env python3
"""Rescale canvas-ds layout from 1920x480 (three 640 areas) to 2048x768 (two 1024 screens).

All horizontal coordinates are normalized to the full canvas width, so the
mapping is linear: x_new = x_old * 1.5 (0.333 -> 0.5, 0.666 -> 1.0).
Vertical values stay unchanged (each screen is 4:3 in both cases).

Only the first (x) component of these tags is scaled:
  pos, size, maxSize, w, logoSize and the layout variables listed in VARS.
minSize is scaled too (background images use it to cover the canvas).
Tags with attributes (e.g. ifSubset) and storyboard animations of the x
position are handled as well.
The theme root gets defaultView="detailed", so the "Automatic" gamelist
style always uses the list instead of ES's unstyled basic view.
Carousel item sizes (itemsize, itemSizeCarousel) are NOT scaled: ES
multiplies them by the carousel size, which is already scaled.
Children of grid tiles are skipped, because their coordinates are relative
to the tile, not to the screen.
"""
import re
import sys

FACTOR = 1.5
TAGS = {"pos", "size", "maxSize", "minSize", "w", "logoSize"}
VARS = {"gamelistPos", "gamelistSize",
        "gamelistBackgroundPos", "gamelistBackgroundSize",
        "gamelistShadowPos", "gamelistShadowSize"}
SCALE = TAGS | VARS

def fmt(v):
    s = ("%.6f" % v).rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"

tag_re = re.compile(r"<(?P<tag>[A-Za-z]+)(?P<attrs>(?:\s[^>]*)?)>(?P<val>[^<]*)</(?P=tag)>")
open_re = re.compile(r"<(?P<tag>[A-Za-z]+)(?P<attrs>[^>]*)>")

def process(text, log, fname):
    out = []
    skip_stack = []  # tags whose content must not be scaled
    anim_x = [False]
    lines = text.split("\n")
    for ln, line in enumerate(lines, 1):
        # track entering/leaving grid-tile blocks
        for m in open_re.finditer(line):
            tag, attrs = m.group("tag"), m.group("attrs")
            if attrs.strip().endswith("/"):
                continue
            if tag in ("gridtile", "itemTemplate") or 'name="gridtile.' in attrs:
                skip_stack.append(tag)
        def repl(m):
            tag, val = m.group("tag"), m.group("val")
            if tag not in SCALE or skip_stack:
                return m.group(0)
            parts = val.split()
            if not parts:
                return m.group(0)
            try:
                x = float(parts[0])
            except ValueError:
                return m.group(0)  # ${variable} – scaled where it is defined
            nx = x * FACTOR
            q = round(nx * 4) / 4          # snap 0.3333*1.5 -> 0.5 etc.
            if abs(nx - q) < 0.001:
                nx = q
            new = " ".join([fmt(nx)] + parts[1:])
            log.append(f"{fname}:{ln}: <{tag}> {val.strip()} -> {new}")
            return f"<{tag}{m.group('attrs')}>{new}</{tag}>"
        line = tag_re.sub(repl, line)
        # storyboard animations on the x position (from="..." to="...")
        if 'property="x"' in line:
            anim_x[0] = True
        if anim_x[0] and not skip_stack:
            def arepl(m):
                v = float(m.group(2)) * FACTOR
                q = round(v * 4) / 4
                if abs(v - q) < 0.001: v = q
                log.append(f"{fname}:{ln}: anim x {m.group(1)}={m.group(2)} -> {fmt(v)}")
                return f'{m.group(1)}="{fmt(v)}"'
            line = re.sub(r'\b(from|to)="(-?[0-9.]+)"', arepl, line)
        if anim_x[0] and "/>" in line:
            anim_x[0] = False
        # "Automatic" gamelist style: the theme root gets defaultView="detailed",
        # so ES always uses the (restyled) list instead of its unstyled basic view.
        if line.startswith("<theme ") and "defaultView" not in line:
            line = line.replace("<theme ", '<theme defaultView="detailed" ', 1)
            log.append(f'{fname}:{ln}: defaultView="detailed"')
        out.append(line)
        # closing tags after processing the line
        for tag in re.findall(r"</([A-Za-z]+)>", line):
            if skip_stack and skip_stack[-1] == tag:
                skip_stack.pop()
    return "\n".join(out)

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    files = sys.argv[3:]
    log = []
    for f in files:
        with open(f"{src}/{f}", encoding="utf-8") as fh:
            text = fh.read()
        new = process(text, log, f)
        import os
        os.makedirs(os.path.dirname(f"{dst}/{f}") or dst, exist_ok=True)
        with open(f"{dst}/{f}", "w", encoding="utf-8") as fh:
            fh.write(new)
    print("\n".join(log))
    print(f"\n{len(log)} values scaled", file=sys.stderr)
