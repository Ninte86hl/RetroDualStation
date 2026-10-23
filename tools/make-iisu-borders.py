#!/usr/bin/env python3
"""iiSU-Rahmen fürs Installationspaket vorbereiten (statt ~100 MB Archiv-Download auf dem Gerät).

Aufruf (im Repo-Ordner):
    git clone --depth 1 https://github.com/viik4/iisu-asset-tool /tmp/iisu
    python3 tools/make-iisu-borders.py /tmp/iisu <Artwork-Manager-Repo>
Legt artworkmanager/borders/<system>/<name>-<hash>.png an – gleiche Auswahl und Dateinamen
wie prepare_iisu_borders() beim Entpacken des Archivs (Quelle: iisu-asset-tool, MIT-Lizenz).
"""
import hashlib, os, shutil, sys
from pathlib import Path

src, am = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(am))
from rocknixds_artwork_manager.iisu_borders import IISU_BORDER_ALIASES, _is_png, _normalized


def border_name_matches_system(name, system):
    """Genauer Namensvergleich (die Teilwort-Suche ordnete z. B. GENESIS/SNES dem NES zu)."""
    stem = _normalized(Path(name).stem)
    return any(stem == _normalized(a) or stem == 'nintendo' + _normalized(a) for a in IISU_BORDER_ALIASES[system])

out = Path(__file__).resolve().parent.parent / "artworkmanager" / "borders"
shutil.rmtree(out, ignore_errors=True)
files = sorted(p for p in src.rglob("*.png") if "/borders/" in p.as_posix().casefold())
for system in IISU_BORDER_ALIASES:
    seen = set()                                   # gleiche Bilder (borders/ + android/) nur einmal
    for p in files:
        if not border_name_matches_system(p.name, system):
            continue
        if system == "nds" and "3ds" in p.stem.casefold():   # Alias „ds“ trifft sonst auch den 3DS
            continue
        data = p.read_bytes()
        if not _is_png(data) or hashlib.sha1(data).digest() in seen:
            continue
        seen.add(hashlib.sha1(data).digest())
        arch = "iisu-asset-tool-main/" + p.relative_to(src).as_posix()   # Pfad wie im Archiv
        suffix = hashlib.sha1(arch.encode("utf-8")).hexdigest()[:8]
        d = out / system
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{p.stem}-{suffix}.png").write_bytes(data)
for d in sorted(out.iterdir()):
    print(d.name, len(list(d.glob("*.png"))), sum(f.stat().st_size for f in d.glob("*.png")) // 1024, "KiB")
