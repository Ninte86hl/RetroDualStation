"""Mehrteilige Spiele (Disc 1, Disc 2 …) zu einer .m3u zusammenfassen.

- Die .m3u listet die CDs; RetroArch wechselt sie über das Disc-Menü.
- In der gamelist.xml bekommt die .m3u die Spieldaten von CD 1, die einzelnen
  CDs werden mit <hidden>true</hidden> ausgeblendet. Nichts wird gelöscht oder verschoben.
"""
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

DISC = re.compile(r"^(?P<base>.+?)\s*[\(\[](?:Disc|Disk|CD)\s*(?P<n>\d+)(?:\s*of\s*\d+)?[\)\]](?P<rest>.*)$", re.I)
DISC_EXT = {".chd", ".cue", ".pbp", ".iso", ".ccd", ".toc", ".img", ".bin"}


def _clean_base(base, rest):
    """„Final Fantasy VII (Europe)“ + „ (En,Fr)“ → Name der .m3u ohne Disc-Angabe."""
    return (base + rest).strip()


def find_groups(folder):
    """{m3u-Name: [CD-Dateien in Reihenfolge]} für alle Spiele mit mindestens zwei CDs
    und noch ohne .m3u. .bin wird nur genommen, wenn es keine .cue dazu gibt."""
    folder = Path(folder)
    if not folder.is_dir():
        return {}
    files = sorted(p.name for p in folder.iterdir() if p.is_file())
    have_cue = {Path(f).stem.casefold() for f in files if f.lower().endswith(".cue")}
    groups = {}
    for f in files:
        ext = Path(f).suffix.lower()
        if ext not in DISC_EXT or (ext == ".bin" and Path(f).stem.casefold() in have_cue):
            continue
        if ext in (".bin", ".img") and any(x.lower().endswith((".cue", ".ccd", ".toc")) for x in files
                                           if Path(x).stem.casefold() == Path(f).stem.casefold()):
            continue
        m = DISC.match(Path(f).stem)
        if not m:
            continue
        key = _clean_base(m["base"], m["rest"]) + ".m3u"
        groups.setdefault(key, []).append((int(m["n"]), f))
    out = {}
    for m3u, discs in groups.items():
        discs.sort()
        names = [f for _n, f in discs]
        if len(names) >= 2 and not (folder / m3u).exists():
            out[m3u] = names
    return out


def referenced_by_m3u(folder):
    """Dateinamen, die in einer .m3u des Ordners stehen (für die Spieleliste ausblenden)."""
    refs = set()
    for m3u in Path(folder).glob("*.m3u"):
        try:
            for line in m3u.read_text(errors="replace").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    refs.add(Path(line.replace("\\", "/")).name.casefold())
        except OSError:
            pass
    return refs


def apply_groups(folder, groups):
    """.m3u-Dateien schreiben und die gamelist.xml anpassen. Gibt die Anzahl zurück."""
    folder = Path(folder)
    gl = folder / "gamelist.xml"
    root = ET.parse(gl).getroot() if gl.is_file() and gl.stat().st_size else ET.Element("gameList")
    by_path = {}
    for g in root.findall("game"):
        p = (g.findtext("path") or "").replace("\\", "/")
        by_path[Path(p).name.casefold()] = g
    for m3u, discs in groups.items():
        tmp = folder / (m3u + ".rds-tmp")
        tmp.write_text("\n".join(discs) + "\n")
        os.replace(tmp, folder / m3u)
        first = by_path.get(discs[0].casefold())
        entry = ET.SubElement(root, "game")
        ET.SubElement(entry, "path").text = "./" + m3u
        if first is not None:                       # Spieldaten von CD 1 übernehmen
            for child in first:
                if child.tag not in ("path", "hidden"):
                    e = ET.SubElement(entry, child.tag, child.attrib)
                    e.text = child.text
        name = entry.find("name")
        clean = Path(m3u).stem
        clean = re.sub(r"\s*[\(\[][^)\]]*[\)\]]", "", clean).strip() or clean
        if name is None:
            ET.SubElement(entry, "name").text = clean
        else:
            name.text = DISC.sub(lambda m: m["base"] + m["rest"], name.text or clean).strip() or clean
        for d in discs:                              # einzelne CDs ausblenden
            g = by_path.get(d.casefold())
            if g is None:
                g = ET.SubElement(root, "game")
                ET.SubElement(g, "path").text = "./" + d
            h = g.find("hidden")
            if h is None:
                h = ET.SubElement(g, "hidden")
            h.text = "true"
    if gl.is_file():
        (folder / "gamelist.xml.vor-m3u").write_bytes(gl.read_bytes())
    ET.indent(root)
    tmp = folder / "gamelist.xml.rds-tmp"
    ET.ElementTree(root).write(tmp, encoding="utf-8", xml_declaration=True)
    os.replace(tmp, gl)
    return len(groups)
