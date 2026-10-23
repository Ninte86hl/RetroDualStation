#!/usr/bin/env python3
"""iiSU-Rahmen fürs Installationspaket vorbereiten (statt ~100 MB Archiv-Download auf dem Gerät).

Aufruf (im Repo-Ordner):
    git clone --depth 1 https://github.com/viik4/iisu-asset-tool /tmp/iisu
    python3 tools/make-iisu-borders.py /tmp/iisu
Legt artworkmanager/borders/<name>-<hash>.png und systems.txt (Bild → Systemordner) an;
der Installer verteilt sie nach data/platform-borders/<system>/.
Quelle: iisu-asset-tool von viik4 (MIT-Lizenz).
"""
import hashlib, shutil, sys
from pathlib import Path

BY_BORDER = {   # Rahmen → Systemordner aus /storage/roms (ROCKNIX)
    "NES": "nes famicom fds nesh", "SNES": "snes sfc snesh snesmsu1 satellaview sufami",
    "GENESIS": "genesis genh megadrive megadrive-japan megadriveh",
    "Game_Boy": "gb gbh", "Game_Boy_Color": "gbc gbch", "Game_Boy_Advance": "gba gbah gbav",
    "NINTENDO_DS": "nds ndsiware", "NINTENDO_3DS": "3ds", "N64": "n64 n64dd",
    "Gamecube": "gamecube", "Wii": "wii wiiware",
    "PSX": "psx", "PS2": "ps2", "PSP": "psp pspminis", "PS_Vita": "psvita",
    "Saturn": "saturn", "Dreamcast": "dreamcast", "Game_Gear": "gamegear gamegearh",
    "Neo_Geo_Pocket_Color": "ngp ngpc",
    "Arcade": "arcade mame fbneo cps1 cps2 cps3 neogeo naomi atomiswave st-v",
    "PC": "pc windows",
}
PNG = bytes((137, 80, 78, 71, 13, 10, 26, 10))


def norm(s):
    return "".join(c for c in s.casefold() if c.isalnum())


src = Path(sys.argv[1])
out = Path(__file__).resolve().parent.parent / "artworkmanager" / "borders"
shutil.rmtree(out, ignore_errors=True)
out.mkdir(parents=True)
files = sorted(p for p in src.rglob("*.png") if "/borders/" in p.as_posix().casefold())
lines = []
for border, folders in BY_BORDER.items():
    p = next((f for f in files if norm(f.stem) == norm(border) and f.read_bytes().startswith(PNG)), None)
    if not p:
        print("fehlt:", border)
        continue
    arch = "iisu-asset-tool-main/" + p.relative_to(src).as_posix()   # Dateiname wie beim Archiv
    name = f"{p.stem}-{hashlib.sha1(arch.encode('utf-8')).hexdigest()[:8]}.png"
    (out / name).write_bytes(p.read_bytes())
    lines.append(f"{name} {folders}")
(out / "systems.txt").write_text("\n".join(lines) + "\n")
print(len(lines), "Rahmen,", sum(f.stat().st_size for f in out.glob("*.png")) // 1024, "KiB")
