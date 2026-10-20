#!/usr/bin/env python3
"""RetroDualStation Artwork Manager – die Gerätefassung des RocknixDS Artwork Managers.

Oberer Bildschirm: großes Artwork (Kandidat) zum Vergleichen.
Unterer Bildschirm: System, Spieleliste, Suche und Bedienung (Touch + Tasten).

Such-, Erkennungs- und Schreiblogik kommen unverändert aus dem Paket
rocknixds_artwork_manager; nur der Gerätezugriff läuft lokal statt über SSH.
Zeichnen, Bildschirme, Eingabe und Bildschirmtastatur kommen vom Kontrollcenter.
"""
import ctypes
import json
import os
import subprocess
import sys
import threading
import time
import traceback
from io import BytesIO
from pathlib import Path

BASE = "/storage/.config/retrodualstation"
BTN_THUMBL = 317                                # linker Stick drücken
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, BASE + "/lib", BASE + "/controlcenter",
          os.path.join(os.path.dirname(HERE), "controlcenter")):
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

import rds_cc as cc                                   # noqa: E402
from rds_cc import (Overlay, Pen, Keyboard, THEMES, load_config, log, grab,   # noqa: E402
                    open_event, read_events, find_event, abs_range, TouchReader,
                    EV_SYN, EV_KEY, EV_ABS, ABS_HAT0X, ABS_HAT0Y, DPAD,
                    BTN_SOUTH, BTN_EAST, BTN_NORTH, BTN_WEST, BTN_TL, BTN_TR, BTN_START,
                    BTN_MODE, BTN_Z, BTN_SELECT, JOYPAD_NAME, HOME_NAME, TOUCH_NAME, PI)
from PIL import Image                                 # noqa: E402

from rocknixds_artwork_manager.app_controller import AppController          # noqa: E402
from rocknixds_artwork_manager.device import Device                         # noqa: E402
from rocknixds_artwork_manager.systems import SYSTEMS, ARCADE_SYSTEM_KEYS    # noqa: E402
from rocknixds_artwork_manager.iisu import display_name_from_rom, search_name_from_rom  # noqa: E402
from rocknixds_artwork_manager.game_identity import (clone_international_search_names,  # noqa: E402
                                                     international_search_names, parse_nointro_dat)
from rocknixds_artwork_manager.game_identity_source import load_libretro_nointro_dat, load_nointro_clone_list  # noqa: E402
from rocknixds_artwork_manager.release_metadata import load_tosec_dat, tosec_release_year  # noqa: E402
from rocknixds_artwork_manager.arcade_names import arcade_entry, load_fbneo_dat, parse_fbneo_dat  # noqa: E402
from rocknixds_artwork_manager.artwork_http import iidb_request, iidb_asset_pages, sgdb_request, download_artwork  # noqa: E402
from rocknixds_artwork_manager.artwork_cache import cached_download         # noqa: E402
from rocknixds_artwork_manager.artwork_sources import (search_artwork_games, artwork_candidates_for_games,  # noqa: E402
                                                       manual_search_rows)
from rocknixds_artwork_manager.settings import steamgriddb_key  # noqa: E402
from rocknixds_artwork_manager.nointro import normalize_name  # noqa: E402
from rocknixds_artwork_manager.icon_generator import IconEditSettings, render_iisu_icon  # noqa: E402
from rocknixds_artwork_manager.iisu_borders import prepare_iisu_borders, border_candidates  # noqa: E402
from rocknixds_artwork_manager.device_profiles import target_for  # noqa: E402

VERSION = "0.1.0"
# Programm und alle Daten liegen im Ports-Ordner (am PC leicht erreichbar, z. B. per Netzwerkfreigabe)
WORK = Path(os.environ.get("RDS_ARTWORK_DIR", "/storage/roms/ports/artworkmanager"))
SETTINGS = WORK / "settings.json"          # interne Einstellungen (Sicherungsfrage)
CFG = WORK / "settings.cfg"                 # vom Nutzer bearbeitbar, z. B. am PC
CFG_TEMPLATE = """# RetroDualStation Artwork Manager – Einstellungen
# Diese Datei kann am PC bearbeitet werden. Leere Werte = nicht gesetzt.

# SteamGridDB API-Key (kostenlos: https://www.steamgriddb.com/profile/preferences/api)
steamgriddb_api_key=
"""
PREVIEW_DIR = Path("/tmp/rds-artwork")
KINDS = [("boxart", "Boxart"), ("cartridge", "Cartridge"), ("image", "Image")]
# Raster des unteren Bildschirms (Entwurfskoordinaten 1260 × 951, wie im Kontrollcenter)
LIST_Y, ROW_H, ROWS = 100, 74, 9            # Listen: 9 sichtbare Zeilen
TABS_Y, TABS_H = 28, 78                     # Artwork-Stile (Spielname steht oben)
GAL_Y = 120                                 # Bildleiste
# Kachelform je Artwork-Stil: (Breite, Höhe) – Hülle hochkant, Cartridge quadratisch, Hero breit
TILE_SIZE = {"boxart": (330, 495), "cartridge": (370, 370), "image": (385, 125)}
TILES = 3                                   # immer drei Kacheln, mittig
TILE_GAP = 22


def tile_geom(kind):
    """Breite, Höhe, Schrittweite und Anzahl voll sichtbarer Kacheln."""
    if kind in VERTICAL:
        w, h = VERTICAL[kind]
        return w, h, h + TILE_GAP, 2
    w, h = TILE_SIZE[kind]
    return w, h, w + TILE_GAP, TILES


VERTICAL = {"image": (900, 290)}           # Hero-Bilder: zwei untereinander
BAR_Y, BAR_H = 800, 86                      # A/B/X/Y-Leiste
HINT_Y = 930                                # Hinweiszeile


# ------------------------------------------------------------- Gerät lokal ----

class LocalDevice(Device):
    """Wie Device, aber die Befehle laufen direkt auf dem Gerät statt über SSH."""

    def __init__(self, host="localhost", runner=subprocess.run):
        self.host = "localhost"
        self._runner = runner
        self.ssh = []
        self.control_path = ""

    def _run(self, command, input_data=None):
        try:
            r = subprocess.run(["sh", "-c", command], input=input_data, timeout=60,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Befehl hat zu lange gedauert") from exc
        if r.returncode:
            raise RuntimeError(r.stderr.decode("utf-8", "replace").strip() or "Befehl fehlgeschlagen")
        return r.stdout

    def close(self):
        pass


def read_cfg():
    """settings.cfg lesen (anlegen, falls sie fehlt) und den API-Key bereitstellen."""
    WORK.mkdir(parents=True, exist_ok=True)
    if not CFG.exists():
        CFG.write_text(CFG_TEMPLATE)
    values = {}
    for line in CFG.read_text(errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip('"')
    key = values.get("steamgriddb_api_key", "")
    if key:
        os.environ["STEAMGRIDDB_API_KEY"] = key
    else:
        os.environ.pop("STEAMGRIDDB_API_KEY", None)
    return values


def write_cfg_key(value):
    """Eingabe am Gerät in settings.cfg übernehmen (übrige Zeilen bleiben)."""
    text = CFG.read_text(errors="replace") if CFG.exists() else CFG_TEMPLATE
    lines, done = [], False
    for line in text.splitlines():
        if line.strip().startswith("steamgriddb_api_key"):
            line, done = f"steamgriddb_api_key={value}", True
        lines.append(line)
    if not done:
        lines.append(f"steamgriddb_api_key={value}")
    CFG.write_text("\n".join(lines) + "\n")
    read_cfg()


def load_settings():
    try:
        return json.loads(SETTINGS.read_text())
    except (OSError, ValueError):
        return {}


def save_settings(data):
    WORK.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1))
    tmp.replace(SETTINGS)


def to_png(data, path, limit=900):
    """Beliebiges Bild (PNG/JPG/WebP) für die Anzeige verkleinert als PNG speichern."""
    img = Image.open(BytesIO(data))
    img.load()
    img = img.convert("RGBA")
    img.thumbnail((limit, limit))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    img.save(tmp, "PNG")
    tmp.replace(path)
    return img.size


_C = cc.cairo
for _fn, _args, _res in (("cairo_pattern_create_linear", [ctypes.c_double] * 4, ctypes.c_void_p),
                         ("cairo_pattern_add_color_stop_rgba", [ctypes.c_void_p] + [ctypes.c_double] * 5, None),
                         ("cairo_set_source", [ctypes.c_void_p, ctypes.c_void_p], None),
                         ("cairo_pattern_destroy", [ctypes.c_void_p], None),
                         ("cairo_rectangle", [ctypes.c_void_p] + [ctypes.c_double] * 4, None),
                         ("cairo_fill", [ctypes.c_void_p], None)):
    getattr(_C, _fn).argtypes, getattr(_C, _fn).restype = _args, _res


def fade(P, x, y, w, h):
    """Senkrechter Verlauf von durchsichtig nach Schwarz."""
    X, Y, W, H = P.X(x), P.Y(y), w * P.s, h * P.s
    pat = _C.cairo_pattern_create_linear(0.0, Y, 0.0, Y + H)
    _C.cairo_pattern_add_color_stop_rgba(pat, 0.0, 0.0, 0.0, 0.0, 0.0)
    _C.cairo_pattern_add_color_stop_rgba(pat, 1.0, 0.0, 0.0, 0.0, 1.0)
    _C.cairo_rectangle(P.cr, X, Y, W, H)
    _C.cairo_set_source(P.cr, pat)
    _C.cairo_fill(P.cr)
    _C.cairo_pattern_destroy(pat)


# ------------------------------------------------------------- Sprache ----
# Der Manager folgt wie das Kontrollcenter der Sprache von EmulationStation.
# Übersetzt wird beim Zeichnen (AmPen), damit der übrige Code deutsch bleiben kann.
EN_AM = {
    "Leerzeichen": "Space", "Abbrechen": "Cancel",
    "Eigenes Bild": "Own image",
    "Filter": "Filter", "Keine Spiele für diesen Filter": "No games for this filter",
    "Spieleliste": "Game list", "Filter: alle · fehlende · keine Artworks": "Filter: all · missing · no artwork",
    "Editor: 1:1-Bild mit iiSU-Rahmen gestalten": "Editor: create a 1:1 image with iiSU border",
    "Editor – Cartridge": "Editor – Cartridge", "1:1 mit iiSU-Rahmen": "1:1 with iiSU border",
    "Rahmen": "Border", "Zoom": "Zoom", "Position": "Position", "Größe": "Size", "Zurücksetzen": "Reset",
    "verschieben": "move", "Kein Rahmen": "No border", "Editor-Vorschau": "Editor preview",
    "Das Ergebnis wird als Cartridge übernommen.": "The result is taken as the cartridge image.",
    "Editor wird vorbereitet …": "Preparing editor …",
    "Für dieses System gibt es keinen iiSU-Rahmen": "There is no iiSU border for this system",
    "Editor-Bild als Cartridge übernommen": "Editor image taken as cartridge",
    "Mehrteilige Spiele zusammenfassen (M3U)": "Merge multi-disc games (M3U)", "Zusammenfassen": "Merge",
    "Keine mehrteiligen Spiele ohne M3U gefunden": "No multi-disc games without M3U found",
    "M3U-Dateien werden erstellt …": "Creating M3U files …",
    "Je Spiel entsteht eine .m3u. In EmulationStation erscheint es nur noch einmal,":
        "Each game gets an .m3u. EmulationStation shows it only once,",
    "in RetroArch wechselst du die CD über das Disc-Menü. Nichts wird gelöscht.":
        "and RetroArch switches discs via the disc menu. Nothing is deleted.",
    "Artwork Manager": "Artwork Manager", "Willkommen": "Welcome", "Die Funktionen": "Features",
    "Voraussetzung": "Requirement", "Sicherung": "Backup",
    "Der Artwork Manager ergänzt Bilder in einer bestehenden Spieleliste.":
        "The Artwork Manager adds images to an existing game list.",
    "Jedes System braucht deshalb eine gamelist.xml in seinem ROM-Ordner.":
        "Every system therefore needs a gamelist.xml in its ROM folder.",
    "Systeme ohne Liste sind in der Systemliste markiert.": "Systems without a list are marked in the system list.",
    "So entsteht die Spieleliste": "How to create the game list",
    "Im Single-Screen-Modus (originale ROCKNIX-Oberfläche) mit dem Scraper":
        "In single-screen mode (original ROCKNIX interface), use the scraper",
    "die Spiele einmal scrapen. Die Liste gilt auch für RetroDualStation.":
        "to scrape your games once. The list is also used by RetroDualStation.",
    "Gespeichert wird in der gamelist.xml und im Ordner images des Systems.":
        "Images are saved to the gamelist.xml and the system's images folder.",
    "Systemliste": "System list", "Spielansicht": "Game view",
    "Einzelsuche: ein Spiel aus der Spieleliste bearbeiten": "Single search: edit one game from the game list",
    "Mehrfachsuche: alle Spiele mit fehlenden Artworks nacheinander":
        "Batch search: all games with missing artwork, one after another",
    "Spiel suchen über alle Systeme": "Search games across all systems", "Einstellungen": "Settings",
    "Bild wählen": "Choose image", "Artwork-Stil": "Artwork style", "übernehmen": "take",
    "speichern": "save", "anderes Spiel suchen": "search another game", "Ansicht oben": "top view",
    "Vor dem ersten Speichern pro System automatisch eine": "Automatically create a backup before the first",
    "Sicherung anlegen (gamelist.xml und vorhandene Artworks)?": "save per system (gamelist.xml and existing artwork)?",
    "Empfohlen. Die Sicherung liegt danach unter": "Recommended. Backups are stored in",
    "Ja, sichern": "Yes, back up", "Nein": "No", "Weiter": "Next",
    "System wählen": "Choose system", "Einzelsuche": "Single search", "Mehrfachsuche": "Batch search",
    "Spiel wählen": "Choose game", "Seite": "Page", "wählen": "choose", "ändern": "change",
    "wiederherstellen": "restore", "überspringen": "skip",
    "Öffnen": "Open", "Auswählen": "Select", "Ändern": "Change", "Wiederherstellen": "Restore",
    "Beenden": "Quit", "Zurück": "Back", "Spiel suchen": "Search game", "Editor": "Editor",
    "Übernehmen": "Take", "Abwählen": "Remove", "Batch beenden": "End batch",
    "Spiel suchen (alle Systeme)": "Search game (all systems)", "SteamGridDB API-Key": "SteamGridDB API key",
    "keine Spieleliste": "no game list", "gesetzt": "set", "fehlt": "missing", "an": "on", "aus": "off",
    "Sicherung vor dem Speichern": "Backup before saving", "Kurzanleitung anzeigen": "Show quick guide",
    "Sicherung wiederherstellen": "Restore backup", "Sicherungen aufräumen": "Clean up backups",
    "Zwischenspeicher leeren": "Clear cache", "Log leeren": "Clear log",
    "Sicherung ausschalten?": "Turn off backups?", "Trotzdem ausschalten": "Turn off anyway", "Abbrechen": "Cancel",
    "Ohne Sicherung lässt sich ein Fehler nicht auf dem Gerät rückgängig machen.":
        "Without a backup, mistakes cannot be undone on the device.",
    "Geht etwas schief, wird ein PC benötigt, um gamelist.xml und":
        "If something goes wrong, a PC is needed to restore",
    "die Artworks wiederherzustellen.": "the gamelist.xml and the artwork.",
    "gamelist.xml und die gesicherten Artworks dieses Systems werden":
        "The gamelist.xml and backed-up artwork of this system will be",
    "auf diesen Stand zurückgesetzt. Spätere Änderungen gehen verloren.":
        "reset to this state. Later changes will be lost.",
    "Artwork wird gespeichert": "Saving artwork", "Artwork-Stile": "Artwork styles",
    "Wird vorbereitet …": "Preparing …", "Bilder werden zugeschnitten …": "Cropping images …",
    "Sicherung wird erstellt …": "Creating backup …", "Wird gespeichert und geprüft …": "Saving and verifying …",
    "Gespeichert": "Saved", "Artworks werden gesucht …": "Searching artwork …",
    "Verbinde mit EmulationStation …": "Connecting to EmulationStation …",
    "Suche läuft …": "Searching …", "Suche in allen Systemen …": "Searching all systems …",
    "Sicherung wird wiederhergestellt …": "Restoring backup …",
    "Keine Bilder für diesen Artwork-Stil": "No images for this artwork style",
    "Nichts gefunden": "Nothing found", "Keine Bilder": "No images", "Lädt …": "Loading …",
    "Vorschau nicht verfügbar": "Preview not available", "Vorschau": "Preview",
    "✓ übernommen": "✓ taken", "– fehlt": "– missing", "– keine Bilder": "– no images",
    "Image – lädt …": "Image – loading …", "Image – noch nicht gewählt": "Image – not chosen yet",
    "Großansicht": "Large view", "Mix-Ansicht": "Mix view", "Speichern": "Save",
    "alle Artworks": "all artwork", "teilweise": "partial", "keine": "none",
    "Kein Spiel gefunden": "No game found", "Keine Treffer – anderen Namen probieren": "No results – try another name",
    "Keine Artworks gefunden – mit Y anderes Spiel suchen": "No artwork found – press Y to search another game",
    "Keine Spieleliste – im Single-Screen-Modus mit dem Scraper anlegen":
        "No game list – create one with the scraper in single-screen mode",
    "Erst mit A ein Bild übernehmen, dann mit Start speichern": "Take an image with A first, then save with Start",
    "Alle Stile übernommen – mit Start speichern": "All styles taken – save with Start",
    "Alle Spiele haben bereits alle Artworks": "All games already have all artwork",
    "Noch keine Sicherungen vorhanden": "No backups yet", "Zwischenspeicher geleert": "Cache cleared",
    "Log geleert": "Log cleared", "Spiel in diesem System nicht gefunden": "Game not found in this system",
    "SteamGridDB-Key gespeichert": "SteamGridDB key saved", "SteamGridDB-Key entfernt": "SteamGridDB key removed",
    "Sicherheitsprüfung fehlgeschlagen – nichts geschrieben": "Safety check failed – nothing was written",
    "Speichern nicht vollständig bestätigt": "Saving could not be fully verified",
}
EN_AM_PATTERNS = [
    (r"^(.*) · (alle|fehlende|keine Artworks)$",
     lambda m: f"{m[1]} · " + {"alle": "all", "fehlende": "missing", "keine Artworks": "no artwork"}[m[2]]),
    (r"^(\d+) gefunden$", lambda m: f"{m[1]} found"),
    (r"^(\d+) mehrteilige Spiele zusammenfassen\?$", lambda m: f"Merge {m[1]} multi-disc games?"),
    (r"^(\d+) Spiele zusammengefasst$", lambda m: f"{m[1]} games merged"),
    (r"^Beispiel: (.*)$", lambda m: f"Example: {m[1]}"),
    (r"^(\d+) Spiele$", lambda m: f"{m[1]} games"),
    (r"^Suche: (.*)$", lambda m: f"Search: {m[1]}"),
    (r"^Vorschau (\d+ / \d+)$", lambda m: f"Preview {m[1]}"),
    (r"^(\d+) vorhanden$", lambda m: f"{m[1]} available"),
    (r"^(\d+) Artworks\.?$", lambda m: f"{m[1]} artworks"),
    (r"^Start  Speichern \((\d+)\)$", lambda m: f"Start  Save ({m[1]})"),
    (r"^(.*) wird geladen …$", lambda m: f"Loading {m[1]} …"),
    (r"^(.*) wiederherstellen\?$", lambda m: f"Restore {m[1]}?"),
    (r"^Stand vom (.*) · (\d+) Artworks\.$", lambda m: f"State of {m[1]} · {m[2]} artworks."),
    (r"^(.*): Stand vom (.*) wiederhergestellt$", lambda m: f"{m[1]}: restored state of {m[2]}"),
    (r"^(\d+) ältere Sicherung\(en\) gelöscht – die neueste je System bleibt$",
     lambda m: f"{m[1]} older backup(s) deleted – the newest per system is kept"),
    (r"^Sicherung vor dem Speichern: (an|aus)$", lambda m: "Backup before saving: " + ("on" if m[1] == "an" else "off")),
    (r"^Batch beendet · (\d+) gespeichert · (\d+) übersprungen(?: · (\d+) offen)?$",
     lambda m: f"Batch finished · {m[1]} saved · {m[2]} skipped" + (f" · {m[3]} open" if m[3] else "")),
    (r"^(\d+ / \d+) · einmalige Frage$", lambda m: f"{m[1]} · asked once"),
    (r"^Fehler: (.*)$", lambda m: f"Error: {m[1]}"),
]


def am_tr(text):
    """Deutsch → Englisch für die Oberfläche (nur wenn ES nicht auf Deutsch steht)."""
    if cc.LANG[0] == "de" or not isinstance(text, str) or not text:
        return text
    if text in EN_AM:
        return EN_AM[text]
    for pre in (" – ", "  ", "✓ "):                      # Hinweis-Teile, Haken
        if text.startswith(pre) and text[len(pre):] in EN_AM:
            return pre + EN_AM[text[len(pre):]]
    import re as _re
    for pat, fn in EN_AM_PATTERNS:
        m = _re.match(pat, text)
        if m:
            return fn(m)
    return text


class AmPen(Pen):
    """Pen, der Oberflächentexte des Artwork Managers übersetzt."""

    def text(self, txt, size, x, y, c, bold=False, align="l", raw=False):
        return super().text(am_tr(txt), size, x, y, c, bold=bold, align=align, raw=True)

    def width(self, txt, size, bold=False, raw=False):
        return super().width(am_tr(txt), size, bold=bold, raw=True)


from multidisc import find_groups, apply_groups, referenced_by_m3u  # noqa: E402


OWN = WORK / "eigene"                       # eigene Bilder: eigene/, eigene/<system>/, eigene/alle/
OWN_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def fetch(url):
    """Bild holen: eigene Datei (file://) direkt, sonst über den Zwischenspeicher aus dem Netz."""
    if url.startswith("file://"):
        return Path(url[7:]).read_bytes()
    return cached_download(WORK / "data" / "cache", url, download_artwork)


def own_images(system, rom, names):
    """Eigene Bilder für ein Spiel: Dateiname = Spiel- oder ROM-Name (in eigene/ oder eigene/<system>/),
    dazu alles aus eigene/alle/."""
    try:
        for d in (OWN, OWN / "alle"):
            d.mkdir(parents=True, exist_ok=True)
    except OSError:
        return []
    wanted = {normalize_name(n) for n in list(names) + [display_name_from_rom(rom)] if n}
    files = []
    for folder in (OWN / system, OWN):
        if folder.is_dir():
            files += [f for f in sorted(folder.iterdir()) if f.is_file() and f.suffix.lower() in OWN_EXT
                      and normalize_name(display_name_from_rom(f.name)) in wanted]
    files += [f for f in sorted((OWN / "alle").iterdir()) if f.is_file() and f.suffix.lower() in OWN_EXT]
    out, seen = [], set()
    for f in files:
        if str(f) in seen:
            continue
        seen.add(str(f))
        url = "file://" + str(f)
        out.append({"id": "own-" + f.name, "url": url, "preview_url": url, "source": "Eigenes Bild",
                    "_own": True})
    return out


def has_gamelist(system):
    return os.path.isfile(f"/storage/roms/{system}/gamelist.xml")


def hint_parts(*pairs):
    """Hinweiszeile nach der RetroDualStation-Regel: Taste fett, dann „– Erklärung“.
    hint_parts("▲ ▼", "wählen", "Start", "Einzelsuche") → ▲ ▼ – wählen · Start – Einzelsuche"""
    out = []
    for n in range(0, len(pairs), 2):
        if n:
            out.append(("  ·  ", False))
        out += [(pairs[n], True), (" – " + pairs[n + 1], False)]
    return out


def is_2x3(w, h):
    """True bei Hochformat 2:3 (mit Toleranz), False sonst, None wenn die Größe unbekannt ist."""
    try:
        w, h = int(w or 0), int(h or 0)
    except (TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    return abs(w / h - 2 / 3) <= 0.08


def by_style(cands):
    """Jeder Tab zeigt nur Bilder seines Artwork-Stils.

    Boxart:    iiDB „Box Art“ (echte Hüllen) und alle SteamGridDB-Hüllen (600×900)
    Cartridge: iiDB iiSU-Box-Art (1:1 mit Rahmen) und Icons, alle SteamGridDB-Icons und 1:1-Grids
    Image:     alle SteamGridDB-Heroes

    Achtung: SteamGridDB hat ein eigenes Feld „style“ (alternate, official …);
    iiDB-Bilder erkennt man an ihrer Kennung „iidb-…“.
    """
    def iidb(c):
        return str(c.get("id") or "").startswith("iidb-")

    def iidb_style(c):
        return c.get("style") if iidb(c) else None

    out = {
        "boxart": [c for c in cands.get("boxart", [])
                   if (not iidb(c) or iidb_style(c) == "boxart") and is_2x3(c.get("width"), c.get("height")) is not False],
        "cartridge": [c for c in cands.get("cartridge", []) + cands.get("boxart", [])
                      if (iidb(c) and iidb_style(c) in ("iisu_boxart", "icon"))
                      or (not iidb(c) and c in cands.get("cartridge", []))],
        "image": [c for c in cands.get("image", []) if not iidb(c)],
    }
    for k, items in out.items():   # doppelte URLs entfernen, Reihenfolge behalten
        seen, uniq = set(), []
        for c in items:
            if c.get("url") not in seen:
                seen.add(c.get("url"))
                uniq.append(c)
        out[k] = uniq
    return out


# ---------------------------------------------------------------- Zustand ----

class App:
    def __init__(self):
        self.cfg = load_config()                       # Theme/Akzent/Tastatur wie im Kontrollcenter
        cc.LANG[0] = cc.ui_language()                  # Sprache wie EmulationStation
        self.T = THEMES.get(self.cfg.get("theme"), THEMES["dark"])
        self.accent = (self.cfg.get("accent") or "#e5383b").lstrip("#")
        self.settings = load_settings()
        read_cfg()
        self.pen = None
        self.hits = []
        self.kbd = None
        self.touch = None
        self.dirty = True
        self.top_dirty = True
        self.quit = False
        self.changed = False                          # etwas geschrieben → ES neu laden
        self.busy = None                              # Text während Arbeit im Hintergrund
        self.message = None                           # (Text, Zeit) kurze Meldung
        self.view = "setup" if "backup" not in self.settings else "start"
        self.sel = 0                                  # Auswahl in der aktuellen Liste
        self.scroll = 0
        self.app = None
        self.systems = []
        self.system = None
        self.games = []                               # [(rom, name, status)]
        self.backed_up = set()
        self.fbneo = None
        self.nointro = {}
        # geöffnetes Spiel
        self.rom = None
        self.title = ""
        self.cands = {k: [] for k, _ in KINDS}
        self.idx = {k: 0 for k, _ in KINDS}
        self.chosen = {}                              # kind -> Kandidat
        self.kind = 0
        self.current = {}                             # kind -> PNG-Pfad des vorhandenen Artworks
        self.previews = {}                            # url -> PNG-Pfad | None (Fehler) | "…" (lädt)
        self.gscroll = {}                             # kind -> erste sichtbare Kachel
        self.sizes = {}                               # PNG-Pfad -> (Breite, Höhe)
        self.loader = threading.Semaphore(3)
        self.saving = None                            # Ladebildschirm beim Speichern
        self.saving_until = 0.0
        self.settings_from = 0
        self.gfilter = 0                              # Spieleliste: 0 alle · 1 fehlende · 2 keine Artworks
        self._md_cache = None                          # gefundene mehrteilige Spiele
        self.intro = 0                                # Seite der Einführung beim ersten Start
        self.origin = "games"                         # wohin die Spielansicht zurückführt
        self.last_rom = None
        self.gsel = 0
        self.top_mode = "mix"                         # oben: "mix" (alle Stile) oder "single" (Großansicht)
        self.gquery = ""
        self.gresults = []                            # Spielsuche über alle Systeme
        self.backups = []                             # Liste zum Wiederherstellen
        self.confirm = None                           # Rückfrage (A ja / B nein)
        self.batch = None                             # laufender Batch
        self.pending = None                           # Folgeaktion nach Hintergrundarbeit
        self.after_saving = None                      # Folgeaktion nach dem Ladebildschirm
        self.results = []                             # Trefferliste der Suche
        self.query = ""

    # -- Hilfen --
    def say(self, text):
        self.message = (text, time.monotonic())
        self.dirty = True

    def work(self, label, fn, then=None):
        """fn im Hintergrund ausführen; Fehler werden angezeigt statt abzubrechen.
        then() läuft danach im Hauptthread (nur wenn fn erfolgreich war)."""
        if self.busy:
            return
        self.busy = label
        self.dirty = True

        def run():
            ok = False
            try:
                fn()
                ok = True
            except Exception as exc:
                log("Fehler:\n" + traceback.format_exc().rstrip())
                self.say(f"Fehler: {exc}")
            finally:
                self.busy = None
                if ok and then:
                    self.pending = then
                self.dirty = self.top_dirty = True
        threading.Thread(target=run, daemon=True).start()

    def _focus_ring(self, P, x, y, w, h, r):
        """Wie im Kontrollcenter – wird von der Bildschirmtastatur benutzt."""
        P.rrect(x - 5, y - 5, w + 10, h + 10, r + 5, self.accent, stroke=4)

    def _hit(self, x, y):
        for hx, hy, hw, hh, action in reversed(self.hits):
            if hx <= x <= hx + hw and hy <= y <= hy + hh:
                return action
        return None

    # -- Ablauf --
    def answer_setup(self, backup):
        self.settings["backup"] = bool(backup)
        save_settings(self.settings)
        self.view = "start"
        self.start()

    def start(self):
        def go():
            WORK.mkdir(parents=True, exist_ok=True)
            self.app = AppController("localhost", WORK / "data", device_factory=LocalDevice)
            self.app.connect()
            self.systems = self.app.available_systems()
            self.view, self.sel, self.scroll = "systems", 0, 0
        self.work("Verbinde mit EmulationStation …", go)

    def open_system(self, i, batch=False, then=None):
        s = self.systems[i]

        def go():
            self.app.open_system(s["key"], s["extensions"])
            status = self.app.artwork_status()
            names = {}
            for g in self.app.games():
                path = Path(str(g.get("path") or "").replace("\\", "/")).name.casefold()
                names[path] = (g.get("name") or "").strip()
            self.system = s
            self.games = []
            hidden = referenced_by_m3u(f"/storage/roms/{s['key']}")   # CDs, die eine .m3u zusammenfasst
            for rom in self.app.roms():
                base = Path(str(rom)).name
                if base.casefold() in hidden:
                    continue
                name = names.get(base.casefold()) or display_name_from_rom(base)
                self.games.append((base, name, status.get(base, 0)))
            self.games.sort(key=lambda g: g[1].casefold())
            self.view, self.sel, self.scroll = "games", 0, 0
        self.work(f"{s['name']} wird geladen …", go, then=self.start_batch if batch else then)

    # -- Batch: alle Spiele mit fehlenden Artworks nacheinander --
    def start_batch(self):
        queue = [g[0] for g in self.games if g[2] < 3]
        if not queue:
            self.batch = None
            self.say("Alle Spiele haben bereits alle Artworks")
            return
        self.batch = {"queue": queue, "pos": 0, "saved": 0, "skipped": 0}
        log("Batch:", len(queue), "Spiele")
        self.batch_open()

    def batch_open(self):
        rom = self.batch["queue"][self.batch["pos"]]
        i = next((n for n, g in enumerate(self.games) if g[0] == rom), 0)
        self.sel = i
        self.open_game(i)

    def batch_next(self, saved):
        b = self.batch
        if not b:
            return
        b["saved" if saved else "skipped"] += 1
        b["pos"] += 1
        if b["pos"] < len(b["queue"]):
            self.batch_open()
        else:
            self.batch_end()

    def batch_end(self):
        b, self.batch = self.batch, None
        if not b:
            return
        rest = len(b["queue"]) - b["pos"]
        self.say(f"Batch beendet · {b['saved']} gespeichert · {b['skipped']} übersprungen"
                 + (f" · {rest} offen" if rest > 0 else ""))
        self.leave_game("systems")

    def leave_game(self, where=None):
        """Spielansicht verlassen: zurück dorthin, wo die Suche gestartet wurde.
        Einzelsuche → Spieleliste, Batch → Systemliste, Spielsuche (Y) → deren Trefferliste."""
        where = where or self.origin
        self.rom = None
        if where == "systems":
            self.view = "systems"
            self.sel = next((n for n, s in enumerate(self.systems) if s is self.system), 0)
            self.scroll = max(0, self.sel - ROWS + 1)
        elif where == "gsearch" and self.gresults:
            self.view = "gsearch"
            self.sel = self.gsel
            self.scroll = max(0, self.sel - ROWS + 1)
        else:
            self.view = "games"
            self.sel = next((n for n, g in enumerate(self.vgames()) if g[0] == self.last_rom),
                            min(self.sel, max(0, len(self.vgames()) - 1)))
            self.scroll = max(0, min(self.scroll, self.sel), self.sel - ROWS + 1)
        self.top_dirty = self.dirty = True

    # Suchnamen wie im PC-Manager
    def _arcade(self, rom):
        if self.system["key"] not in ARCADE_SYSTEM_KEYS:
            return None
        if self.fbneo is None:
            self.fbneo = parse_fbneo_dat(load_fbneo_dat(WORK / "data"))
        return arcade_entry(self.fbneo, rom)

    def _international(self, rom):
        key = self.system["key"]
        sysdef = SYSTEMS.get(key)
        if not sysdef or not sysdef.nointro_dat:
            return []
        try:
            if key not in self.nointro:
                self.nointro[key] = (parse_nointro_dat(load_libretro_nointro_dat(WORK / "data", sysdef.nointro_dat)),
                                     load_nointro_clone_list(WORK / "data", key))
            games, clones = self.nointro[key]
            names = (clone_international_search_names(games, rom, clones) if clones else []) \
                + international_search_names(games, rom)
        except Exception as exc:
            log("No-Intro-Namen nicht verfügbar:", exc)
            return []
        out = []
        for n in names:
            if n and n.casefold() not in {x.casefold() for x in out}:
                out.append(n)
        return out

    def open_game(self, i, forced=None, name=None, then=None):
        rom, title, _st = self.games[i]
        self.rom, self.title = rom, title
        self.last_rom = rom
        if self.batch:
            self.origin = "systems"
        self.cands = {k: [] for k, _ in KINDS}
        self.idx = {k: 0 for k, _ in KINDS}
        self.gscroll = {}
        self.chosen = {}
        self.kind = 0
        self.view = "game"
        key = self.system["key"]

        def go():
            self.current = {}
            for kind, info in (self.app.existing_artwork(rom) or {}).items():
                if info.get("data"):
                    path = PREVIEW_DIR / "current" / f"{kind}.png"
                    try:
                        to_png(info["data"], path, 400)
                        self.current[kind] = str(path)
                    except Exception:
                        pass
            self.top_dirty = True
            arcade = self._arcade(rom)
            intl = self._international(rom)
            rom_name = arcade["search"] if arcade else search_name_from_rom(title if key in ARCADE_SYSTEM_KEYS
                                                                            else display_name_from_rom(rom))
            search = name or (intl[0] if intl else rom_name)
            alts = [n for n in intl + [rom_name] if n and n.casefold() != search.casefold()]
            year = None
            try:
                year = arcade["year"] if arcade else tosec_release_year(load_tosec_dat(WORK / "data", key), search)
            except Exception:
                pass
            api = steamgriddb_key()
            sgdb = sgdb_request(api) if api else None
            sysdef = SYSTEMS.get(key)
            result = search_artwork_games(search, key, sysdef.name if sysdef else key, iidb_request, sgdb,
                                          release_year=year, sgdb_alternatives=alts)
            for provider, item in (forced or {}).items():
                result[provider] = item
            log(f"Suche: {search} · iiDB {(result.get('iidb') or {}).get('id')} · "
                f"SteamGridDB {(result.get('steamgriddb') or {}).get('id')}")
            pages = iidb_asset_pages(result["iidb"]["id"]) if result.get("iidb") else {}
            raw = artwork_candidates_for_games(result, pages, sgdb)
            self.cands = by_style(raw)
            own = own_images(key, rom, [title, search, rom_name])     # eigene Bilder vorn in allen Tabs
            for k in self.cands:
                self.cands[k] = own + self.cands[k]
            if own:
                log(f"  eigene Bilder: {len(own)}")
            for c in list(self.cands["boxart"]):   # Größe unbekannt (iiDB): gleich laden und prüfen
                if is_2x3(c.get("width"), c.get("height")) is None:
                    self._load_preview(c)
            for k, _label in KINDS:   # Vergleich mit dem PC-Manager: gefunden → angezeigt
                srcs = {}
                for c in raw.get(k, []):
                    src = c.get("style") or c.get("source") or "?"
                    srcs[src] = srcs.get(src, 0) + 1
                log(f"  {k}: gefunden {len(raw.get(k, []))} {srcs} → angezeigt {len(self.cands.get(k, []))}")
            self.query = search
            if not any(self.cands.values()):
                self.say("Keine Artworks gefunden – mit Y anderes Spiel suchen")
            self.kind = next((n for n, (k, _) in enumerate(KINDS) if self.cands.get(k)), 0)
            self.want_previews()
        self.work("Artworks werden gesucht …", go, then=then)

    FILTERS = ["alle", "fehlende", "keine Artworks"]

    def vgames(self):
        """Spieleliste nach Filter: alle · fehlende (rot und gelb) · nur rote."""
        if self.gfilter == 1:
            return [g for g in self.games if g[2] < 3]
        if self.gfilter == 2:
            return [g for g in self.games if g[2] == 0]
        return self.games

    def real_index(self, i):
        """Index in der sichtbaren Liste → Index in self.games."""
        vis = self.vgames()
        return self.games.index(vis[i]) if 0 <= i < len(vis) else 0

    def next_filter(self):
        rom = self.vgames()[self.sel][0] if self.vgames() else None
        self.gfilter = (self.gfilter + 1) % len(self.FILTERS)
        vis = self.vgames()
        self.sel = next((n for n, g in enumerate(vis) if g[0] == rom), 0)
        self.scroll = max(0, self.sel - ROWS + 1)
        if not vis:
            self.say("Keine Spiele für diesen Filter")

    def game_to_editor(self, i=None):
        """X in der Spieleliste: Spiel öffnen und direkt in den Editor springen."""
        i = self.real_index(self.sel if i is None else i)
        if not self.vgames():
            return
        self.origin = "games"

        def then():
            for n, (k, _l) in enumerate(KINDS):   # Quelle: erste Boxart, sonst ein anderes Bild
                if self.cands.get(k):
                    self.kind, self.idx[k] = n, 0
                    break
            if self.cand():
                self.open_editor()
            else:
                self.say("Keine Bilder gefunden – mit Y anderes Spiel suchen")
        self.open_game(i, then=then)

    def kind_key(self):
        return KINDS[self.kind][0]

    def cand(self, kind=None):
        kind = kind or self.kind_key()
        items = self.cands.get(kind) or []
        return items[self.idx[kind]] if items else None

    def want_previews(self):
        """Vorschaubilder der sichtbaren Kacheln im Hintergrund laden."""
        kind = self.kind_key()
        items = self.cands.get(kind) or []
        first = self.gscroll.get(kind, 0)
        tiles = tile_geom(kind)[3]
        for j in range(max(0, first - 1), min(len(items), first + tiles + 2)):
            self._load_preview(items[j])

    def _load_preview(self, item):
        url = item.get("preview_url") or item.get("thumb") or item.get("url")
        if not url or url in self.previews:
            return
        self.previews[url] = "…"

        def go():
            with self.loader:          # höchstens drei Downloads gleichzeitig
                try:
                    data = fetch(url)
                    path = PREVIEW_DIR / "cand" / (str(abs(hash(url))) + ".png")
                    size = to_png(data, path)
                    self.previews[url] = str(path)
                    if item in (self.cands.get("boxart") or []) and not item.get("_own") and is_2x3(*size) is False:
                        self.drop_boxart(item)
                except Exception as exc:
                    log("Vorschau nicht ladbar:", url, exc)
                    self.previews[url] = None
            self.top_dirty = self.dirty = True
        threading.Thread(target=go, daemon=True).start()

    def drop_boxart(self, item):
        """Kein 2:3-Format: aus dem Boxart-Tab entfernen, Auswahl stabil halten."""
        items = self.cands.get("boxart") or []
        if item not in items:
            return
        i = items.index(item)
        cur = self.idx["boxart"]
        self.cands["boxart"] = items[:i] + items[i + 1:]
        if i < cur or cur >= len(self.cands["boxart"]):
            self.idx["boxart"] = max(0, cur - 1)
        if self.chosen.get("boxart") is item:
            del self.chosen["boxart"]
        self.gscroll["boxart"] = min(self.gscroll.get("boxart", 0), max(0, len(self.cands["boxart"]) - TILES))
        log("Boxart ausgeblendet (kein 2:3):", item.get("url"))
        if self.kind_key() == "boxart":
            self.want_previews()

    def preview_of(self, item):
        if not item:
            return None
        return self.previews.get(item.get("preview_url") or item.get("thumb") or item.get("url"))

    def select(self, i):
        """Kachel i des aktuellen Artwork-Stils wählen und sichtbar halten."""
        kind = self.kind_key()
        n = len(self.cands.get(kind) or [])
        if not n:
            return
        i = max(0, min(n - 1, i))
        self.idx[kind] = i
        first = self.gscroll.get(kind, 0)
        if i < first:
            first = i
        elif i >= first + tile_geom(kind)[3]:
            first = i - tile_geom(kind)[3] + 1
        self.gscroll[kind] = first
        self.want_previews()
        self.top_dirty = True

    def step(self, d):
        self.select(self.idx[self.kind_key()] + d)

    def scroll_gallery(self, d):
        kind = self.kind_key()
        n = len(self.cands.get(kind) or [])
        self.gscroll[kind] = max(0, min(max(0, n - tile_geom(kind)[3]), self.gscroll.get(kind, 0) + d))
        self.want_previews()

    def switch_kind(self, d):
        self.kind = (self.kind + d) % len(KINDS)
        self.want_previews()
        self.top_dirty = True

    def toggle_choice(self):
        """A: Bild übernehmen (oder wieder abwählen) und zum nächsten Artwork-Stil mit Bildern springen."""
        kind, c = self.kind_key(), self.cand()
        if not c:
            return
        if self.chosen.get(kind) is c:
            del self.chosen[kind]
        else:
            self.chosen[kind] = c
            for d in range(1, len(KINDS)):
                k = (self.kind + d) % len(KINDS)
                if self.cands.get(KINDS[k][0]) and KINDS[k][0] not in self.chosen:
                    self.kind = k
                    self.want_previews()
                    break
            else:
                self.say("Alle Stile übernommen – mit Start speichern")
        self.top_dirty = True

    def transfer(self):
        if not self.chosen:
            self.say("Erst mit A ein Bild übernehmen, dann mit Start speichern")
            return
        rom, chosen, system = self.rom, dict(self.chosen), self.system["key"]
        self.saving = {"title": self.title,
                       "kinds": [label for k, label in KINDS if k in chosen],
                       "step": "Wird vorbereitet …", "done": False}

        def go():
            if self.settings.get("backup") and system not in self.backed_up:
                self.saving["step"] = "Sicherung wird erstellt …"
                self.dirty = True
                b = self.app.backup_artwork()
                self.backed_up.add(system)
                log("Sicherung:", b.get("path"))
            self.saving["step"] = "Bilder werden zugeschnitten …"
            self.dirty = True
            from_web = {k: v for k, v in chosen.items() if not v.get("_png")}
            if from_web:
                self.app.stage_scraper_artwork(rom, from_web,
                                               lambda url: fetch(url))
            for k, v in chosen.items():           # im Editor gestaltet: fertiges PNG
                if v.get("_png"):
                    self.app.stage_artwork(rom, k, v["_png"])
            preview = self.app.preview()
            media = preview.get("media") or []
            if not media or (preview.get("set") or {}).get("rom") != rom or (preview.get("xml") or {}).get("games_changed") != 1:
                raise RuntimeError("Sicherheitsprüfung fehlgeschlagen – nichts geschrieben")
            self.saving["step"] = "Wird gespeichert und geprüft …"
            self.dirty = True
            r = self.app.commit()
            n = len(media)
            ok = (r.get("ok") and r.get("stage") == "complete" and r.get("media_verified") == n
                  and r.get("media_errors") == 0 and r.get("xml_games_changed") == 1)
            if not ok:
                raise RuntimeError("Speichern nicht vollständig bestätigt")
            self.changed = True
            status = self.app.artwork_status()
            self.games = [(g[0], g[1], status.get(g[0], g[2])) for g in self.games]
            self.chosen = {}
            for kind, info in (self.app.existing_artwork(rom) or {}).items():
                if info.get("data"):
                    path = PREVIEW_DIR / "current" / f"{kind}.png"
                    to_png(info["data"], path, 400)
                    self.current[kind] = str(path)
            self.saving.update(step="Gespeichert", done=True)
            if self.batch:
                self.after_saving = lambda: self.batch_next(True)
            else:
                self.after_saving = self.leave_game
            self.saving_until = time.monotonic() + 1.2      # kurz „Gespeichert“ zeigen

        def run():
            try:
                go()
            except Exception:
                self.saving = None
                raise
        self.work("saving", run)

    # -- Editor: 1:1-Bild mit iiSU-Rahmen --
    def open_editor(self):
        """Das gewählte Bild (beliebiger Stil) als Quelle für ein 1:1-Cartridge-Bild mit Rahmen."""
        c = self.cand()
        if not c:
            return
        system = self.system["key"]

        def go():
            data = fetch(c.get("url") or c.get("preview_url"))
            try:
                prepare_iisu_borders(WORK / "data", system)
            except Exception as exc:
                log("Rahmen nicht ladbar:", exc)
            borders = [b.path for b in border_candidates(WORK / "data", system)]
            target = target_for(self.app.profile, "cartridge") if self.app and self.app.profile else None
            self.editor = {"src": data, "borders": borders, "border": 0, "zoom": 100, "x": 0, "y": 0,
                           "size": target.width if target else 480, "png": None, "path": None, "from": c}
            if not borders:
                self.say("Für dieses System gibt es keinen iiSU-Rahmen")
            self.view = "editor"
            self.editor_render()
        self.work("Editor wird vorbereitet …", go)

    def editor_render(self):
        """Vorschau im Hintergrund neu berechnen (dieselbe Funktion wie im PC-Manager)."""
        ed = self.editor
        if not ed or not ed["borders"]:
            return
        ed["gen"] = ed.get("gen", 0) + 1
        gen = ed["gen"]

        def go():
            try:
                border = Path(ed["borders"][ed["border"]]).read_bytes()
                png = render_iisu_icon(ed["src"], border, IconEditSettings(ed["zoom"], ed["x"], ed["y"]),
                                       size=ed["size"])
            except Exception as exc:
                log("Editor:", exc)
                self.say(f"Fehler: {exc}")
                return
            if self.editor is not ed or ed.get("gen") != gen:
                return                                  # inzwischen geändert – neueres Ergebnis folgt
            path = PREVIEW_DIR / "editor" / f"edit-{gen}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(png)
            old, ed["png"], ed["path"] = ed.get("path"), png, str(path)
            if old and old != ed["path"]:
                try:
                    os.unlink(old)
                except OSError:
                    pass
            self.top_dirty = self.dirty = True
        threading.Thread(target=go, daemon=True).start()

    def editor_move(self, dx, dy):
        ed = self.editor
        step = max(4, ed["size"] // 40)
        ed["x"] = max(-ed["size"], min(ed["size"], ed["x"] + dx * step))
        ed["y"] = max(-ed["size"], min(ed["size"], ed["y"] + dy * step))
        self.editor_render()

    def editor_zoom(self, d):
        ed = self.editor
        ed["zoom"] = max(50, min(220, ed["zoom"] + d))
        self.editor_render()

    def editor_reset(self):
        ed = self.editor
        if ed:
            ed.update(zoom=100, x=0, y=0)
            self.editor_render()

    def editor_next_border(self):
        ed = self.editor
        ed["border"] = (ed["border"] + 1) % len(ed["borders"])
        self.editor_render()

    def editor_take(self):
        """Ergebnis als Cartridge übernehmen und in der Bildleiste vorn einreihen."""
        ed = self.editor
        if not ed or not ed.get("png"):
            return
        n = sum(1 for c in self.cands.get("cartridge", []) if c.get("_png")) + 1
        url = f"editor://{n}"
        item = {"url": url, "preview_url": url, "source": "Editor", "_png": ed["png"]}
        self.previews[url] = ed["path"]
        self.cands["cartridge"] = [item] + list(self.cands.get("cartridge") or [])
        self.kind = next(i for i, (k, _l) in enumerate(KINDS) if k == "cartridge")
        self.idx["cartridge"] = 0
        self.gscroll["cartridge"] = 0
        self.chosen["cartridge"] = item
        self.editor = None
        self.view = "game"
        self.top_dirty = True
        self.say("Editor-Bild als Cartridge übernommen")

    def open_search(self):
        self.kbd = Keyboard(self, "Spiel suchen", self.run_search, secret=False)
        self.kbd.text = self.query or self.title
        self.kbd.cur = len(self.kbd.text)

    def run_search(self, text=None):
        text = (text if isinstance(text, str) else self.kbd.text if self.kbd else self.query).strip()
        self.kbd = None
        if not text:
            return
        self.query = text

        def go():
            api = steamgriddb_key()
            rows = manual_search_rows(text, iidb_request, sgdb_request(api) if api else None)
            # gleiches Spiel aus beiden Quellen nur einmal zeigen
            merged = {}
            for r in rows:
                key = normalize_name(r["name"]).replace(" ", "")
                m = merged.setdefault(key, {"name": r["name"], "console": "", "year": "", "forced": {}})
                provider = "iidb" if r["source"] == "iiDB" else "steamgriddb"
                if provider in m["forced"]:          # zweiter Treffer derselben Quelle → eigene Zeile
                    key += "#" + str(len(merged))
                    m = merged.setdefault(key, {"name": r["name"], "console": "", "year": "", "forced": {}})
                m["forced"][provider] = r["item"]
                if r["console"] != "–" and not m["console"]:
                    m["console"] = r["console"]
                if r["year"] != "–" and not m["year"]:
                    m["year"] = str(r["year"])
            self.results = list(merged.values())
            self.view, self.sel, self.scroll = "search", 0, 0
            if not self.results:
                self.say("Keine Treffer – anderen Namen probieren")
        self.work("Suche läuft …", go)

    def pick_result(self, i):
        row = self.results[i]
        gi = next((n for n, g in enumerate(self.games) if g[0] == self.rom), 0)
        self.open_game(gi, forced=dict(row["forced"]), name=row["name"])

    def edit_key(self):
        def done(text=None):
            value = (text if isinstance(text, str) else self.kbd.text if self.kbd else "").strip()
            self.kbd = None
            write_cfg_key(value)
            self.say("SteamGridDB-Key gespeichert" if value else "SteamGridDB-Key entfernt")
        self.kbd = Keyboard(self, "SteamGridDB API-Key", done, secret=True)

    # -- Bedienung --
    def list_len(self):
        return {"systems": len(self.systems), "games": len(self.vgames()), "search": len(self.results),
                "settings": len(self.setting_rows()), "gsearch": len(self.gresults),
                "restore": len(self.backups)}.get(self.view, 0)

    def move(self, d):
        n = self.list_len()
        if not n:
            return
        self.sel = max(0, min(n - 1, self.sel + d))
        if self.sel < self.scroll:
            self.scroll = self.sel
        elif self.sel >= self.scroll + ROWS:
            self.scroll = self.sel - ROWS + 1

    def activate(self, i=None):
        i = self.sel if i is None else i
        if self.busy:
            return
        if self.view == "systems":
            if self.systems and not has_gamelist(self.systems[i]["key"]):
                self.say("Keine Spieleliste – im Single-Screen-Modus mit dem Scraper anlegen")
            elif self.systems:
                self.open_system(i)
        elif self.view == "settings":
            rows = self.setting_rows()
            if 0 <= i < len(rows):
                rows[i][2]()
        elif self.view == "gsearch" and self.gresults:
            self.pick_global(i)
        elif self.view == "restore" and self.backups:
            self.ask_restore(i)
        elif self.view == "games" and self.vgames():
            self.origin = "games"
            self.open_game(self.real_index(i))
        elif self.view == "search" and self.results:
            self.pick_result(i)

    def back(self):
        if self.kbd:
            self.kbd.back()
            return
        if self.busy:
            return
        if self.view == "editor":
            self.editor = None
            self.view = "game"
            self.top_dirty = True
            return
        if self.view == "game" and self.batch:
            self.batch_end()
            return
        if self.view == "search":
            self.view = "game"
        elif self.view == "settings":
            self.view, self.sel, self.scroll = "systems", self.settings_from, 0
        elif self.view == "gsearch":
            self.view, self.sel, self.scroll = "systems", 0, 0
        elif self.view == "restore":
            self.view, self.sel, self.scroll = "settings", 4, 0
        elif self.view == "game":
            self.leave_game()
        elif self.view == "games":
            self.view = "systems"
            self.sel = next((n for n, s in enumerate(self.systems) if s is self.system), 0)
            self.scroll = max(0, self.sel - ROWS + 1)
        else:
            self.quit = True
        self.top_dirty = True

    def buttons(self):
        """Belegung der festen A/B/X/Y-Leiste je Ansicht: (Taste, Text, Aktion | None)."""
        if self.view == "editor":
            ed = self.editor or {}
            return [("A", "Übernehmen", self.editor_take if ed.get("png") else None),
                    ("B", "Abbrechen", self.back),
                    ("X", "Zurücksetzen", self.editor_reset),
                    ("Y", "Rahmen", self.editor_next_border if len(ed.get("borders") or []) > 1 else None)]
        if self.view == "game":
            kind, c = self.kind_key(), self.cand()
            taken = c is not None and self.chosen.get(kind) is c
            return [("A", "Abwählen" if taken else "Übernehmen", self.toggle_choice if c else None),
                    ("B", "Batch beenden" if self.batch else "Zurück", self.back),
                    ("X", "Editor", self.open_editor if c else None),   # 1:1-Bild mit iiSU-Rahmen

                    ("Y", "Spiel suchen", self.open_search)]
        a_label = {"systems": "Öffnen", "games": "Öffnen", "search": "Auswählen", "gsearch": "Öffnen",
                   "settings": "Ändern", "restore": "Wiederherstellen"}.get(self.view, "")
        return [("A", a_label, self.activate if self.list_len() else None),
                ("B⌂" if self.view == "systems" else "B", "Beenden" if self.view == "systems" else "Zurück", self.back),
                ("X", "Einstellungen", self.open_settings) if self.view == "systems" else
                ("X", "Editor", self.game_to_editor) if self.view == "games" and self.games else ("X", "", None),
                ("Y", "Spiel suchen", self.open_global_search) if self.view == "systems" else
                ("Y", "Filter", self.next_filter) if self.view == "games" else ("Y", "", None)]

    # -- Spielsuche über alle Systeme --
    def open_global_search(self):
        self.kbd = Keyboard(self, "Spiel suchen (alle Systeme)", self.run_global_search, secret=False)
        self.kbd.text = self.gquery
        self.kbd.cur = len(self.kbd.text)

    def run_global_search(self, text=None):
        text = (text if isinstance(text, str) else self.kbd.text if self.kbd else "").strip()
        self.kbd = None
        if not text:
            return
        self.gquery = text
        words = normalize_name(text).split()

        def go():
            hits = []
            for si, sysd in enumerate(self.systems):
                try:
                    games = self.app.device.games(sysd["key"])   # Spieleliste von EmulationStation
                except Exception as exc:
                    log("Spieleliste nicht lesbar:", sysd["key"], exc)
                    continue
                for g in games:
                    name = (g.get("name") or "").strip()
                    rom = Path(str(g.get("path") or "").replace("\\", "/")).name
                    hay = normalize_name(name + " " + rom)
                    if rom and all(w in hay for w in words):
                        rd = str(g.get("releasedate") or g.get("releaseDate") or "")
                        year = rd[:4] if rd[:4].isdigit() and rd[:4] != "1970" else ""
                        hits.append({"name": name or display_name_from_rom(rom), "system": sysd["name"],
                                     "year": year, "si": si, "rom": rom})
            hits.sort(key=lambda h: (h["name"].casefold(), h["system"]))
            self.gresults = hits
            self.view, self.sel, self.scroll = "gsearch", 0, 0
            if not hits:
                self.say("Kein Spiel gefunden")
        self.work("Suche in allen Systemen …", go)

    def pick_global(self, i):
        h = self.gresults[i]
        self.gsel = i

        def then():
            gi = next((n for n, g in enumerate(self.games) if g[0].casefold() == h["rom"].casefold()), None)
            if gi is None:
                self.say("Spiel in diesem System nicht gefunden")
                return
            self.sel = gi
            self.scroll = max(0, gi - ROWS + 1)
            self.origin = "gsearch"
            self.open_game(gi)
        self.open_system(h["si"], then=then)

    # -- Rückfrage (A = ja, B = nein) --
    def ask(self, title, lines, yes_label, on_yes):
        self.confirm = {"title": title, "lines": lines, "yes": yes_label, "on_yes": on_yes}

    def answer(self, yes):
        c, self.confirm = self.confirm, None
        if yes and c:
            c["on_yes"]()

    # -- Einstellungen --
    def open_settings(self):
        self.settings_from = self.sel
        self.view, self.sel, self.scroll = "settings", 0, 0

    def setting_rows(self):
        """(Name, Wert, Aktion) der Einstellungsliste."""
        def size(path):
            total = 0
            for root, _d, files in os.walk(path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass
            return total

        def human(n):
            for unit in ("B", "KB", "MB", "GB"):
                if n < 1024 or unit == "GB":
                    return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
                n /= 1024

        backups = sorted((WORK / "data" / "backups").glob("*.zip")) if (WORK / "data" / "backups").is_dir() else []
        log_file = WORK / "manager.log"
        cache = size(WORK / "data" / "cache" / "downloads") + size(PREVIEW_DIR)
        return [
            ("SteamGridDB API-Key", "gesetzt" if steamgriddb_key() else "fehlt", self.edit_key),
            ("Sicherung vor dem Speichern", "an" if self.settings.get("backup") else "aus", self.toggle_backup),
            ("Kurzanleitung anzeigen", "", self.show_intro),
            ("Mehrteilige Spiele zusammenfassen (M3U)", f"{sum(len(g) for g in self.multidisc_groups().values())} gefunden",
             self.ask_multidisc),
            ("Sicherung wiederherstellen", f"{len(backups)} vorhanden", self.open_restore),
            ("Sicherungen aufräumen", f"{len(backups)} · {human(sum(b.stat().st_size for b in backups))}",
             self.prune_backups),
            ("Zwischenspeicher leeren", human(cache), self.clear_cache),
            ("Log leeren", human(log_file.stat().st_size) if log_file.exists() else "–", self.clear_log),
        ]

    def show_intro(self):
        """Einführung erneut zeigen; die Sicherungsfrage bleibt beantwortet."""
        self.intro = 0
        self.view = "intro"

    def toggle_backup(self):
        def set_backup(on):
            self.settings["backup"] = on
            save_settings(self.settings)
            self.say("Sicherung vor dem Speichern: " + ("an" if on else "aus"))
        if not self.settings.get("backup"):
            set_backup(True)
            return
        self.ask("Sicherung ausschalten?",
                 ["Ohne Sicherung lässt sich ein Fehler nicht auf dem Gerät rückgängig machen.",
                  "Geht etwas schief, wird ein PC benötigt, um gamelist.xml und",
                  "die Artworks wiederherzustellen."],
                 "Trotzdem ausschalten", lambda: set_backup(False))

    def open_restore(self):
        """Alle Sicherungen, neueste zuerst."""
        import zipfile
        folder = WORK / "data" / "backups"
        found = []
        for b in sorted(folder.glob("*.zip"), key=lambda f: f.stat().st_mtime, reverse=True) if folder.is_dir() else []:
            try:
                with zipfile.ZipFile(b) as z:
                    m = json.loads(z.read("manifest.json"))
                key = m.get("system") or "?"
                stamp = str(m.get("created") or "")
                try:
                    when = time.strftime("%d.%m.%Y %H:%M", time.strptime(stamp, "%Y-%m-%d_%H-%M-%S"))
                except ValueError:
                    when = stamp
                name = next((x["name"] for x in self.systems if x["key"] == key),
                            SYSTEMS[key].name if key in SYSTEMS else key)
                found.append({"path": b, "system": key, "name": name, "when": when,
                              "files": max(0, len(m.get("files") or []) - 1)})
            except Exception as exc:
                log("Sicherung nicht lesbar:", b, exc)
        self.backups = found
        if not found:
            self.say("Noch keine Sicherungen vorhanden")
            return
        self.view, self.sel, self.scroll = "restore", 0, 0

    def ask_restore(self, i):
        b = self.backups[i]
        self.ask(f"{b['name']} wiederherstellen?",
                 [f"Stand vom {b['when']} · {b['files']} Artworks.",
                  "gamelist.xml und die gesicherten Artworks dieses Systems werden",
                  "auf diesen Stand zurückgesetzt. Spätere Änderungen gehen verloren."],
                 "Wiederherstellen", lambda: self.restore(b))

    def restore(self, b):
        import zipfile

        def go():
            root = Path("/storage/roms") / b["system"]
            with zipfile.ZipFile(b["path"]) as z:
                names = [n for n in z.namelist() if n != "manifest.json"]
                gl = f"{b['system']}/gamelist.xml"
                for n in sorted(names, key=lambda n: n == gl):        # gamelist.xml zuletzt
                    target = (Path("/storage/roms") / n).resolve()
                    if root.resolve() not in target.parents:
                        raise RuntimeError(f"Ungültiger Pfad in der Sicherung: {n}")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if n == gl and target.exists():
                        target.with_name("gamelist.xml.vor-wiederherstellung").write_bytes(target.read_bytes())
                    tmp = target.with_name(target.name + ".rds-tmp")
                    tmp.write_bytes(z.read(n))
                    tmp.replace(target)
            self.changed = True
            if self.system and self.system["key"] == b["system"]:
                self.system = None          # Spieleliste beim nächsten Öffnen neu einlesen
            self.say(f"{b['name']}: Stand vom {b['when']} wiederhergestellt")
            log("Wiederhergestellt:", b["path"])
        self.work("Sicherung wird wiederhergestellt …", go)

    def prune_backups(self):
        """Je System nur die neueste Sicherung behalten."""
        folder = WORK / "data" / "backups"
        newest, removed = {}, 0
        for b in sorted(folder.glob("*.zip"), key=lambda f: f.stat().st_mtime, reverse=True) if folder.is_dir() else []:
            try:   # das System steht in der manifest.json der Sicherung
                import zipfile
                with zipfile.ZipFile(b) as z:
                    system = json.loads(z.read("manifest.json")).get("system") or b.name
            except Exception:
                continue   # unlesbare Datei nicht anfassen
            if system in newest:
                b.unlink()
                removed += 1
            else:
                newest[system] = b
        self.say(f"{removed} ältere Sicherung(en) gelöscht – die neueste je System bleibt")

    def clear_cache(self):
        import shutil
        # nur heruntergeladene Bilder und Vorschauen; iiSU-Rahmen (data/platform-borders) und
        # Namenslisten (data/cache/libretro, tosec …) bleiben, sonst müssten sie neu geladen werden
        for path in (WORK / "data" / "cache" / "downloads", PREVIEW_DIR):
            shutil.rmtree(path, ignore_errors=True)
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        self.previews.clear()
        self.sizes.clear()
        self.say("Zwischenspeicher geleert")

    def multidisc_groups(self):
        """{System: {m3u: [CDs]}} für alle Systeme; zwischengespeichert, bis neu gesucht wird."""
        if self._md_cache is None:
            self._md_cache = {}
            for sysd in self.systems:
                try:
                    g = find_groups(f"/storage/roms/{sysd['key']}")
                except OSError:
                    g = {}
                if g:
                    self._md_cache[sysd["key"]] = g
        return self._md_cache

    def ask_multidisc(self):
        groups = self.multidisc_groups()
        n = sum(len(g) for g in groups.values())
        if not n:
            self.say("Keine mehrteiligen Spiele ohne M3U gefunden")
            return
        example = next(iter(next(iter(groups.values())).keys()))
        self.ask(f"{n} mehrteilige Spiele zusammenfassen?",
                 [f"Beispiel: {Path(example).stem}",
                  "Je Spiel entsteht eine .m3u. In EmulationStation erscheint es nur noch einmal,",
                  "in RetroArch wechselst du die CD über das Disc-Menü. Nichts wird gelöscht."],
                 "Zusammenfassen", self.do_multidisc)

    def do_multidisc(self):
        groups = self.multidisc_groups()

        def go():
            total = 0
            for key, g in groups.items():
                total += apply_groups(f"/storage/roms/{key}", g)
                log("M3U:", key, list(g))
            self._md_cache = None
            self.changed = True
            self.system = None if self.system and self.system["key"] in groups else self.system
            self.say(f"{total} Spiele zusammengefasst")
        self.work("M3U-Dateien werden erstellt …", go)

    def clear_log(self):
        try:
            os.truncate(WORK / "manager.log", 0)
        except OSError:
            pass
        self.say("Log geleert")

    def on_key(self, code):
        if self.view == "intro":
            if code == BTN_EAST:
                self.intro += 1
            if code == BTN_SOUTH or self.intro >= len(self.INTRO):
                self.view, self.sel, self.scroll = "settings", 2, 0
            return
        if self.view == "setup" and self.intro < len(self.INTRO):
            if code == BTN_EAST:
                self.intro += 1
            elif code == BTN_SOUTH and self.intro:
                self.intro -= 1
            return
        if self.view == "setup":
            if code == BTN_EAST:
                self.answer_setup(True)
            elif code == BTN_SOUTH:
                self.answer_setup(False)
            return
        if self.busy or self.saving:
            return
        if self.confirm:
            if code in (BTN_EAST, BTN_SOUTH):
                self.answer(code == BTN_EAST)
            return
        if code == BTN_SOUTH:
            self.back()
            return
        keys = {BTN_EAST: "A", BTN_NORTH: "X", BTN_WEST: "Y"}
        if code in keys:
            act = next((b[2] for b in self.buttons() if b[0] == keys[code]), None)
            if act:
                act()
        elif code in (BTN_TL, BTN_TR) and self.view == "editor":
            self.editor_zoom(-5 if code == BTN_TL else 5)
        elif code in (BTN_TL, BTN_TR):
            d = -1 if code == BTN_TL else 1
            self.switch_kind(d) if self.view == "game" else self.move(d * ROWS)
        elif code == BTN_START and self.view == "game":
            self.transfer()
        elif code == BTN_THUMBL and self.view == "game":
            self.top_mode = "single" if self.top_mode == "mix" else "mix"
            self.top_dirty = True
        elif code == BTN_START and self.view == "systems" and self.systems:
            self.activate()                                  # Einzelsuche (prüft die Spieleliste)
        elif code == BTN_SELECT and self.view == "systems" and self.systems:
            if has_gamelist(self.systems[self.sel]["key"]):
                self.open_system(self.sel, batch=True)       # Mehrfachsuche
            else:
                self.say("Keine Spieleliste – im Single-Screen-Modus mit dem Scraper anlegen")
        elif code == BTN_SELECT and self.view == "game" and self.batch:
            self.batch_next(False)                           # Spiel überspringen

    def on_dir(self, dx, dy):
        if self.busy or self.confirm:
            return
        if self.view == "editor":
            self.editor_move(dx, dy)
            return
        if self.view == "game":
            if self.kind_key() in VERTICAL:
                if dy or dx:
                    self.step(dy or dx)     # Hero: ▲ ▼ (◀ ▶ geht auch)
            elif dx:
                self.step(dx)           # Stil wechselt nur mit L/R oder Antippen
        elif dy:
            self.move(dy)

    def on_tap(self, x, y):
        hit = self._hit(x, y)
        if self.confirm and (not hit or hit[0] != "confirm"):
            return
        if not hit or self.busy:
            return
        kind, val = hit
        if kind == "row":
            if self.sel == val:
                self.activate(val)
            else:
                self.sel = val
        elif kind == "confirm":
            self.answer(val)
        elif kind == "intro":
            self.intro += 1
            if self.view == "intro" and self.intro >= len(self.INTRO):
                self.view, self.sel, self.scroll = "settings", 2, 0
        elif kind == "setup":
            self.answer_setup(val)
        elif kind == "btn" and val:
            val()
        elif kind == "tile":
            if self.idx[self.kind_key()] == val:
                self.toggle_choice()            # zweites Antippen übernimmt
            else:
                self.select(val)
        elif kind == "kind":
            self.kind = val
            self.want_previews()
            self.top_dirty = True

    # -- Touch (Pixel) --
    def touch_down(self, px, py):
        if not self.pen:
            return
        x, y = self.pen.to_design(px, py)
        self.touch = (x, y, x, y)
        if self.kbd:
            self.kbd.touch_down(x, y)

    def touch_move(self, px, py):
        if not (self.pen and self.touch):
            return
        x, y = self.pen.to_design(px, py)
        self.touch = self.touch[:2] + (x, y)
        if self.kbd:
            self.kbd.touch_move(x, y)

    def touch_up(self):
        if not self.touch:
            return
        x0, y0, x1, y1 = self.touch
        self.touch = None
        if self.kbd:
            self.kbd.touch_up(x0, y0, x1, y1)
            return
        dx, dy = x1 - x0, y1 - y0
        if abs(dy) > 60 and abs(dy) > abs(dx) and self.view in ("games", "search", "systems", "settings", "gsearch", "restore"):
            self.move(-round(dy / ROW_H))                 # senkrecht wischen = Liste blättern
            return
        if self.view == "game":
            vertical = self.kind_key() in VERTICAL
            d = dy if vertical else dx
            if abs(d) > 60 and abs(d) > abs(dx if vertical else dy):
                self.scroll_gallery(-round(d / tile_geom(self.kind_key())[2]))  # wischen = Bilder blättern
                return
        self.on_tap(x0, y0)

    # ---------------------------------------------------------- Zeichnen ----
    def header(self, P, title, right=None):
        T = self.T
        rw = P.width(right, 24, raw=True) + 30 if right else 0
        P.clip(40, 20, 1180 - rw, 70)
        P.text(title, 38, 40, 68, T["text"], bold=True, raw=True)
        P.unclip()
        if right:
            P.text(right, 24, 1220, 66, T["muted"], align="r", raw=True)

    def home_icon(self, P, cx, cy, c):
        """Home-/Zurück-Taste: geschwungener Zurückpfeil wie auf dem Gerät."""
        C, cr = cc.cairo, P.cr
        C.cairo_save(cr)
        C.cairo_new_path(cr)
        # Bogen von unten rechts nach oben links
        C.cairo_arc(cr, P.X(cx + 1), P.Y(cy + 1), 9 * P.s, -PI / 2, PI / 2)
        C.cairo_move_to(cr, P.X(cx + 1), P.Y(cy - 8))
        C.cairo_line_to(cr, P.X(cx - 8), P.Y(cy - 8))
        P.color(c)
        C.cairo_set_line_width(cr, 3.2 * P.s)
        C.cairo_stroke(cr)
        # Pfeilspitze nach links
        C.cairo_new_path(cr)
        C.cairo_move_to(cr, P.X(cx - 12), P.Y(cy - 8))
        C.cairo_line_to(cr, P.X(cx - 5), P.Y(cy - 14))
        C.cairo_line_to(cr, P.X(cx - 5), P.Y(cy - 2))
        C.cairo_close_path(cr)
        C.cairo_fill(cr)
        C.cairo_restore(cr)

    def bar(self, P, hint_left, hint_right=""):
        """Feste A/B/X/Y-Leiste und Hinweiszeile ganz unten."""
        T, A = self.T, self.accent
        w, gap, x = (1180 - 3 * 14) / 4, 14, 40
        for n, (key, label, act) in enumerate(self.buttons()):
            on = act is not None
            primary = on and n == 0
            P.rrect(x, BAR_Y, w, BAR_H, 22, A if primary else T["tile"], a=1.0 if on else 0.35)
            cx = x + w / 2
            keys = list(key)                       # z. B. "B⌂" = B oder Home
            tw = P.width(label, 27, bold=True, raw=True) if label else 0
            kw = 42 * len(keys) + 6 * (len(keys) - 1)
            kx = cx - (tw + kw + 10) / 2 + 21 if label else cx - kw / 2 + 21
            for k in keys:
                P.circle(kx, BAR_Y + BAR_H / 2, 21, "ffffff" if primary else T["card"])
                if k == "⌂":
                    self.home_icon(P, kx, BAR_Y + BAR_H / 2, T["text"] if on else T["muted"])
                else:
                    P.text(k, 22, kx, BAR_Y + BAR_H / 2 + 8, A if primary else (T["text"] if on else T["muted"]),
                           bold=True, align="c", raw=True)
                kx += 48
            kx -= 48
            if label:
                P.text(label, 27, kx + 31, BAR_Y + BAR_H / 2 + 10, "ffffff" if primary else
                       (T["text"] if on else T["muted"]), bold=True, raw=True)
            if on:
                self.hits.append((x, BAR_Y, w, BAR_H, ("btn", act)))
            x += w + gap
        # Hinweis: Text oder Liste aus (Text, fett)-Teilen, z. B. [("Start", True), (" Einzelsuche", False)]
        parts = [(hint_left, False)] if isinstance(hint_left, str) else hint_left
        hx = 40
        for txt, bold in parts:
            hx += P.text(txt, 22, hx, HINT_Y, T["text"] if bold else T["muted"], bold=bold, raw=True)
        if hint_right:
            P.text(hint_right, 22, 1220, HINT_Y, T["muted"], align="r", raw=True)

    def draw(self, cr, w, h, _view):
        P = self.pen = AmPen(cr, w, h)
        T = self.T
        P.fill_all(T["bg"])
        self.hits = []
        if self.kbd:
            self.kbd.draw(P)
            return
        saving = self.saving
        if saving:
            self.draw_saving(P, saving)
            return
        self.draw_view(P)
        if self.confirm:
            self.draw_confirm(P, self.confirm)
            return
        busy, message = self.busy, self.message   # Hintergrund-Threads ändern das jederzeit
        if busy:
            P.rrect(230, 380, 800, 150, 30, T["card"])
            P.text(str(busy), 32, 630, 468, T["text"], bold=True, align="c", raw=True)
        elif message and time.monotonic() - message[1] < 4:
            P.rrect(130, BAR_Y - 110, 1000, 90, 26, T["card"])
            P.text(str(message[0]), 28, 630, BAR_Y - 54, T["text"], align="c", raw=True)

    INTRO = [
        ("Willkommen", [
            ("Voraussetzung", True),
            ("Der Artwork Manager ergänzt Bilder in einer bestehenden Spieleliste.", False),
            ("Jedes System braucht deshalb eine gamelist.xml in seinem ROM-Ordner.", False),
            ("Systeme ohne Liste sind in der Systemliste markiert.", False),
            ("", False),
            ("So entsteht die Spieleliste", True),
            ("Im Single-Screen-Modus (originale ROCKNIX-Oberfläche) mit dem Scraper", False),
            ("die Spiele einmal scrapen. Die Liste gilt auch für RetroDualStation.", False),
            ("", False),
            ("Gespeichert wird in der gamelist.xml und im Ordner images des Systems.", False),
        ]),
        ("Die Funktionen", [
            ("Systemliste", True),
            ([("Start", "Einzelsuche: ein Spiel aus der Spieleliste bearbeiten")], False),
            ([("Select", "Mehrfachsuche: alle Spiele mit fehlenden Artworks nacheinander")], False),
            ([("Y", "Spiel suchen über alle Systeme"), ("X", "Einstellungen")], False),
            ("Spieleliste", True),
            ([("X", "Editor"), ("Y", "Filter: alle · fehlende · keine Artworks")], False),
            ("Spielansicht", True),
            ([("◀ ▶", "Bild wählen"), ("L / R", "Artwork-Stil"), ("A", "übernehmen")], False),
            ([("Start", "speichern"), ("Y", "anderes Spiel suchen"), ("L3", "Ansicht oben")], False),
            ([("X", "Editor: 1:1-Bild mit iiSU-Rahmen gestalten")], False),
        ]),
    ]

    def draw_intro(self, P, page):
        T, A = self.T, self.accent
        title, lines = self.INTRO[page]
        total = len(self.INTRO) + (1 if self.view == "setup" else 0)
        self.header(P, title, f"{page + 1} / {total}")
        P.rrect(40, 110, 1180, 620, 30, T["card"])
        y = 180
        for text, head in lines:
            if isinstance(text, list):          # Tasten nach der Regel: fett, dann „– Erklärung“
                P.hint(text, 26, 80, y, T["muted"], T["text"])
            elif text:
                P.text(text, 30 if head else 26, 80, y, T["text"] if head else T["muted"], bold=head, raw=True)
            y += 66 if head else 52
        P.rrect(40, BAR_Y, 1180, BAR_H, 22, A)
        P.hint([("A", "Weiter")], 30, 630, BAR_Y + BAR_H / 2 + 11, "ffffff", "ffffff", align="c")
        self.hits.append((40, BAR_Y, 1180, BAR_H, ("intro", None)))

    def draw_setup(self, P):
        T = self.T
        if self.intro < len(self.INTRO):
            self.draw_intro(P, self.intro)
            return
        self.header(P, "Sicherung", f"{len(self.INTRO) + 1} / {len(self.INTRO) + 1} · einmalige Frage")
        P.rrect(50, 170, 1160, 380, 30, T["card"])
        lines = ["Vor dem ersten Speichern pro System automatisch eine",
                 "Sicherung anlegen (gamelist.xml und vorhandene Artworks)?",
                 "",
                 "Empfohlen. Die Sicherung liegt danach unter",
                 "/storage/roms/ports/artworkmanager/data/backups"]
        for n, line in enumerate(lines):
            P.text(line, 30, 90, 240 + n * 52, T["text"] if n < 2 else T["muted"], raw=True)
        P.rrect(50, 600, 560, 110, 30, self.accent)
        P.hint([("A", "Ja, sichern")], 34, 330, 668, "ffffff", "ffffff", align="c")
        self.hits.append((50, 600, 560, 110, ("setup", True)))
        P.rrect(650, 600, 560, 110, 30, T["tile"])
        P.hint([("B", "Nein")], 34, 930, 668, T["text"], T["text"], align="c")
        self.hits.append((650, 600, 560, 110, ("setup", False)))

    def draw_view(self, P):
        """Die eigentliche Ansicht (ohne Tastatur, Ladebildschirm und Meldungen)."""
        if self.view == "intro":
            self.draw_intro(P, min(self.intro, len(self.INTRO) - 1))
            return
        if self.view == "setup":
            self.draw_setup(P)
        elif self.view in ("systems", "games", "search", "settings", "gsearch", "restore"):
            self.draw_list(P)
        elif self.view == "game":
            self.draw_game(P)
        elif self.view == "editor":
            self.draw_editor(P)
        else:
            self.header(P, "Artwork Manager")

    def draw_editor(self, P):
        T, A = self.T, self.accent
        ed = self.editor or {}
        self.header(P, "Editor – Cartridge", "1:1 mit iiSU-Rahmen")
        P.rrect(30, 100, 460, 460, 24, T["card"])
        if ed.get("path"):
            self.fit(P, ed["path"], 50, 120, 420, 420)
        else:
            P.text("Lädt …" if ed.get("borders") else "Kein Rahmen", 28, 260, 340, T["muted"], align="c", raw=True)
        nb = len(ed.get("borders") or [])
        rows = [("Rahmen", f"{ed.get('border', 0) + 1} / {nb}" if nb else "–"),
                ("Zoom", f"{ed.get('zoom', 100)} %"),
                ("Position", f"{ed.get('x', 0):+d} / {ed.get('y', 0):+d}"),
                ("Größe", f"{ed.get('size', 0)} × {ed.get('size', 0)} px")]
        y = 170
        for label, value in rows:
            P.rrect(520, y - 46, 700, 72, 18, T["card"])
            P.text(label, 28, 550, y, T["text"], bold=True, raw=True)
            P.text(value, 26, 1195, y, T["muted"], align="r", raw=True)
            y += 90
        P.text("Das Ergebnis wird als Cartridge übernommen.", 24, 520, y + 20, T["muted"], raw=True)
        self.bar(P, hint_parts("◀ ▶ ▲ ▼", "verschieben", "L / R", "Zoom"))

    def draw_confirm(self, P, c):
        """Rückfrage über der aktuellen Ansicht: A = ja, B = nein."""
        T, A = self.T, self.accent
        self.hits = []
        P.rrect(0, 0, 1260, 951, 0, "000000", a=0.55)
        P.rrect(110, 200, 1040, 470, 34, T["card"])
        P.text(c["title"], 36, 630, 280, T["text"], bold=True, align="c", raw=True)
        for n, line in enumerate(c["lines"]):
            P.text(line, 25, 630, 350 + n * 42, T["muted"], align="c", raw=True)
        P.rrect(160, 540, 450, 90, 26, A)
        P.hint([("A", c["yes"])], 27, 385, 597, "ffffff", "ffffff", align="c")
        self.hits.append((160, 540, 450, 90, ("confirm", True)))
        P.rrect(650, 540, 450, 90, 26, T["tile"])
        P.hint([("B", "Abbrechen")], 27, 875, 597, T["text"], T["text"], align="c")
        self.hits.append((650, 540, 450, 90, ("confirm", False)))

    def draw_saving(self, P, sv):
        """Kleiner Ladebildschirm: welches Spiel, welche Artwork-Stile."""
        T, A = self.T, self.accent
        self.hits = []
        P.text("Artwork wird gespeichert", 24, 630, 150, T["muted"], align="c", raw=True)
        P.rrect(150, 210, 960, 520, 34, T["card"])
        P.clip(190, 240, 880, 80)
        P.text(sv["title"], 36, 630, 300, T["text"], bold=True, align="c", raw=True)
        P.unclip()
        P.text("Artwork-Stile", 24, 630, 370, T["muted"], align="c", raw=True)
        y = 430
        for label in sv["kinds"]:
            P.text(("✓ " if sv["done"] else "• ") + label, 30, 630, y, "2bb673" if sv["done"] else T["text"],
                   bold=True, align="c", raw=True)
            y += 52
        if not sv["done"]:   # einfacher Fortschrittsbalken (läuft hin und her)
            t = (time.monotonic() * 0.8) % 2
            pos = t if t <= 1 else 2 - t
            P.rrect(300, 640, 660, 14, 7, T["tile"])
            P.rrect(300 + pos * 500, 640, 160, 14, 7, A)
        P.text(sv["step"], 24, 630, 700, T["muted"], align="c", raw=True)

    def draw_list(self, P):
        T, A = self.T, self.accent
        legend = None
        if self.view == "systems":
            title = "Artwork Manager"
            hint = hint_parts("▲ ▼", "System wählen", "Start", "Einzelsuche", "Select", "Mehrfachsuche")
            rows = [(s["name"], f"{s['rom_count']} Spiele" if has_gamelist(s["key"]) else "keine Spieleliste", None)
                    for s in self.systems]
        elif self.view == "settings":
            title, hint = "Einstellungen", hint_parts("▲ ▼", "wählen", "A", "ändern")
            rows = [(name, value, None) for name, value, _act in self.setting_rows()]
        elif self.view == "gsearch":
            title, hint = f"Suche: {self.gquery}", hint_parts("▲ ▼", "Spiel wählen", "L / R", "Seite")
            rows = [(h["name"], " · ".join(x for x in (h["system"], h["year"]) if x), None) for h in self.gresults]
        elif self.view == "restore":
            title, hint = "Sicherung wiederherstellen", hint_parts("▲ ▼", "wählen", "A", "wiederherstellen")
            rows = [(f"{b['name']} · {b['when']}", f"{b['files']} Artworks", None) for b in self.backups]
        elif self.view == "games":
            title, hint = self.system["name"], hint_parts("▲ ▼", "Spiel wählen", "L / R", "Seite")
            if self.gfilter:
                title = f"{title} · {self.FILTERS[self.gfilter]}"
            rows = [(name, None, st) for _rom, name, st in self.vgames()]
            legend = True
        else:
            title, hint = f"Suche: {self.query}", hint_parts("▲ ▼", "Spiel wählen", "L / R", "Seite")
            rows = [(r["name"], " · ".join(x for x in (r["console"], r["year"]) if x) or None, None)
                    for r in self.results]
        self.header(P, title, f"{self.sel + 1} / {len(rows)}" if rows else None)
        for n in range(self.scroll, min(len(rows), self.scroll + ROWS)):
            name, right, st = rows[n]
            y = LIST_Y + (n - self.scroll) * ROW_H
            focus = n == self.sel
            P.rrect(30, y, 1200, ROW_H - 8, 18, T["focus"] if focus else T["card"])
            if focus:
                P.rrect(30, y, 8, ROW_H - 8, 4, A)
            x = 62
            if st is not None:
                col = {0: "e5383b", 1: "f08c00", 2: "f08c00"}.get(st, "2bb673")
                P.circle(72, y + (ROW_H - 8) / 2, 10, col)
                x = 98
            rw = P.width(right, 22, raw=True) + 40 if right else 20
            P.clip(x, y, 1215 - x - rw, ROW_H)
            P.text(name, 28, x, y + (ROW_H - 8) / 2 + 10, T["text"], bold=focus, raw=True)
            P.unclip()
            if right:
                P.text(right, 22, 1205, y + (ROW_H - 8) / 2 + 8, T["muted"], align="r", raw=True)
            self.hits.append((30, y, 1200, ROW_H - 8, ("row", n)))
        if not rows:
            P.text("Nichts gefunden", 30, 630, 400, T["muted"], align="c", raw=True)
        self.bar(P, hint)
        if legend:   # Ampel-Erklärung rechts in der Hinweiszeile
            x = 1220
            for label, col in (("keine", "e5383b"), ("teilweise", "f08c00"), ("alle Artworks", "2bb673")):
                w = P.width(label, 22, raw=True)
                P.text(label, 22, x, HINT_Y, T["muted"], align="r", raw=True)
                P.circle(x - w - 16, HINT_Y - 7, 8, col)
                x -= w + 50

    def draw_game(self, P):
        T, A = self.T, self.accent
        x, w = 30, (1200 - 2 * 14) / 3
        for n, (kind, label) in enumerate(KINDS):
            on = n == self.kind
            P.rrect(x, TABS_Y, w, TABS_H, 20, A if on else T["tile"])
            txt = label
            cnt = str(len(self.cands.get(kind) or []))
            tw = P.width(txt, 26, bold=True, raw=True) + 12 + P.width(cnt, 20, raw=True)
            tx = x + (w - tw) / 2
            P.text(txt, 26, tx, TABS_Y + TABS_H / 2 + 9, "ffffff" if on else T["text"], bold=True, raw=True)
            P.text(cnt, 20, tx + tw, TABS_Y + TABS_H / 2 + 9, "ffffff" if on else T["muted"], align="r", raw=True)
            self.hits.append((x, TABS_Y, w, TABS_H, ("kind", n)))
            x += w + 14
        kind = self.kind_key()
        items = self.cands.get(kind) or []
        cur = self.idx[kind]
        first = self.gscroll.get(kind, 0)
        gy, gh = GAL_Y, BAR_Y - 20 - GAL_Y
        tw_, th, step, tiles = tile_geom(kind)
        if not items:
            P.text("Keine Bilder für diesen Artwork-Stil", 30, 630, gy + gh / 2, T["muted"], align="c", raw=True)
        vertical = kind in VERTICAL
        shown = max(0, min(tiles, len(items) - first))
        x0 = 630 - (shown * step - TILE_GAP) / 2           # Gruppe mittig
        y0 = gy + (gh - (shown * step - TILE_GAP)) / 2
        for j in range(first, first + shown):
            if vertical:                                     # Hero: untereinander
                tx, ty = 630 - tw_ / 2 - 50, y0 + (j - first) * step
            else:
                tx, ty = x0 + (j - first) * step, gy + (gh - th) / 2
            sel = j == cur
            if sel:
                P.rrect(tx - 9, ty - 9, tw_ + 18, th + 18, 24, A)
            P.rrect(tx, ty, tw_, th, 18, T["card"])
            path = self.preview_of(items[j])
            if path and path != "…":
                self.fit(P, path, tx + 8, ty + 8, tw_ - 16, th - 16)
            else:
                P.text("…" if path == "…" or path is None and items[j] else "–", 30, tx + tw_ / 2, ty + th / 2,
                       T["muted"], align="c", raw=True)
            if self.chosen.get(kind) is items[j]:
                P.circle(tx + tw_ - 28, ty + 28, 22, "2bb673")
                P.text("✓", 26, tx + tw_ - 28, ty + 37, "ffffff", bold=True, align="c", raw=True)
            self.hits.append((tx, ty, tw_, th, ("tile", j)))
        if vertical and items:           # Pfeile zum Antippen rechts daneben
            ax = 630 + tw_ / 2 - 50 + 40
            for d, sym, ay in ((-1, "▲", gy + 60), (1, "▼", gy + gh - 160)):
                on = 0 <= cur + d < len(items)
                P.rrect(ax, ay, 100, 100, 24, T["tile"], a=1.0 if on else 0.35)
                P.text(sym, 40, ax + 50, ay + 64, T["text"] if on else T["muted"], align="c", raw=True)
                if on:
                    self.hits.append((ax, ay, 100, 100, ("btn", (lambda dd: lambda: self.step(dd))(d))))
        elif not vertical:
            if first > 0:                # Hinweis: links/rechts geht es weiter
                P.text("‹", 60, 14, gy + gh / 2 + 20, T["muted"], raw=True)
            if len(items) > first + tiles:
                P.text("›", 60, 1246, gy + gh / 2 + 20, T["muted"], align="r", raw=True)
        pos = f"{cur + 1} / {len(items)} · " if items else ""
        self.bar(P, hint_parts("▲ ▼" if vertical else "◀ ▶", "Bild wählen", "L / R", "Artwork-Stil",
                               *(("Select", "überspringen") if self.batch else ())), "")
        # rechts: Start = Speichern (auch antippbar), daneben der Stand
        label = f"Start  Speichern ({len(self.chosen)})"
        w = P.width(label, 22, bold=True, raw=True) + 36
        on = bool(self.chosen)
        P.rrect(1220 - w, HINT_Y - 30, w, 42, 21, A if on else T["tile"], a=1.0 if on else 0.35)
        P.text(label, 22, 1220 - w / 2, HINT_Y - 2, "ffffff" if on else T["muted"], bold=True, align="c", raw=True)
        if on:
            self.hits.append((1220 - w, HINT_Y - 34, w, 50, ("btn", self.transfer)))
        P.text(pos.rstrip(" ·"), 22, 1220 - w - 20, HINT_Y, T["muted"], align="r", raw=True)

    # oberer Bildschirm
    def fit(self, P, path, x, y, w, h):
        """Bild vollständig einpassen (nicht beschneiden)."""
        size = self.sizes.get(path)
        if size is None:
            try:
                size = self.sizes[path] = Image.open(path).size
            except Exception:
                return False
        iw, ih = size
        k = min(w / iw, h / ih)
        dw, dh = iw * k, ih * k
        return P.image(path, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, r=10, stretch=True)

    def draw_top(self, cr, w, h):
        """Oben: Spielname und das gewählte Artwork, so groß wie möglich."""
        P = AmPen(cr, w, h)
        if self.kbd:
            # Während der Eingabe: die Ansicht von unten wandert nach oben, unten hat die Tastatur Platz
            hits = self.hits
            P.fill_all(self.T["bg"])
            try:
                self.draw_view(P)
            finally:
                self.hits = hits                       # Touch-Ziele gehören weiter zum unteren Bildschirm
            P.rrect(0, 0, 1260, 951, 0, "000000", a=0.25)
            return
        P.fill_all("000000")
        if self.view == "editor" and self.editor:
            P.text(self.title, 30, 630, 50, "ffffff", bold=True, align="c", raw=True)
            if self.editor.get("path"):
                self.fit(P, self.editor["path"], 230, 80, 800, 800)
            P.text("Editor-Vorschau", 22, 630, 925, "bdbdbd", align="c", raw=True)
            return
        if self.view not in ("game", "search") or not self.rom:
            P.text("Artwork Manager", 64, 630, 430, "ffffff", bold=True, align="c", raw=True)
            P.text("RetroDualStation", 32, 630, 490, "bdbdbd", align="c", raw=True)
            return
        kind = self.kind_key()
        c = self.cand()
        b = self.batch
        if self.top_mode == "mix":
            self.draw_mix(P)
            if b:
                P.text(f"Batch {b['pos'] + 1} / {len(b['queue'])}", 22, 1220, 40, "ffffff", align="r", raw=True)
            return
        if b:
            P.text(f"Batch {b['pos'] + 1} / {len(b['queue'])}", 22, 1220, 40, "bdbdbd", align="r", raw=True)
        P.clip(30, 10, 1200 - (160 if b else 0), 70)
        P.text(self.title, 36, 630, 60, "ffffff", bold=True, align="c", raw=True)
        P.unclip()
        path = self.preview_of(c)
        if path and path != "…":
            self.fit(P, path, 40, 95, 1180, 840)
        else:
            P.text("Lädt …" if path == "…" else "Keine Bilder" if not c else "Vorschau nicht verfügbar",
                   34, 630, 520, "bdbdbd", align="c", raw=True)
        if c and self.chosen.get(kind) is c:
            P.rrect(1000, 870, 220, 56, 28, "2bb673")
            P.text("✓ übernommen", 24, 1110, 906, "ffffff", bold=True, align="c", raw=True)
        P.hint([("L3", "Mix-Ansicht")], 18, 40, 925, "8a8a8a", "bdbdbd")


    def cover(self, P, path, x, y, w, h):
        """Bild füllend (beschnitten) zeichnen."""
        return P.image(path, x, y, w, h, r=0, stretch=False)

    def draw_mix(self, P):
        """Mix-Ansicht: Hero als Hintergrund, Boxart links, Cartridge unter dem Namen.
        Übernommene Bilder tragen ✓, das gerade unten gewählte Bild steht als „Vorschau“ an seinem Platz."""
        A = self.accent
        cur_kind, cur = self.kind_key(), self.cand()

        def slot(kind):
            """(Pfad, Zustand): Zustand "ok" (übernommen), "pv" (Vorschau) oder None (fehlt)."""
            if kind == cur_kind and cur is not None and self.chosen.get(kind) is not cur:
                return self.preview_of(cur), "pv"
            if kind in self.chosen:
                return self.preview_of(self.chosen[kind]), "ok"
            return None, None

        def tag(text, x, y, ok):
            w = P.width(text, 18, bold=True, raw=True) + 26
            P.rrect(x, y, w, 36, 18, "2bb673" if ok else A)
            P.text(text, 18, x + 13, y + 25, "ffffff", bold=True, raw=True)

        def empty(x, y, w, h, label):
            P.rrect(x, y, w, h, 16, "151515")
            P.rrect(x, y, w, h, 16, "5a5a5a", stroke=3)
            P.text(label, 22, x + w / 2, y + h / 2 + 8, "8a8a8a", align="c", raw=True)

        # Image (Hero) oben über die ganze Breite, unten ins Schwarz auslaufend
        hp, hs = slot("image")
        HY, HH = 0, 430
        if hp and hp != "…":
            self.cover(P, hp, 0, HY, 1260, HH)
            fade(P, 0, HY + HH * 0.4, 1260, HH * 0.6 + 2)   # Verlauf nach unten ins Schwarz
            if hs == "pv":
                P.rrect(4, 4, 1252, HH - 8, 0, A, stroke=6)
            tag("✓ Image" if hs == "ok" else "Vorschau", 1080, 20, hs == "ok")
        else:
            P.rrect(0, HY, 1260, HH, 0, "151515")
            P.text("Image – lädt …" if hp == "…" else "Image – noch nicht gewählt", 22, 630, 200, "8a8a8a",
                   align="c", raw=True)

        # Boxart links
        bp, bs = slot("boxart")
        BX, BY, BW, BH = 45, 250, 330, 495
        if bp and bp != "…":
            P.rrect(BX, BY, BW, BH, 16, "000000")
            self.fit(P, bp, BX, BY, BW, BH)
            if bs == "pv":
                P.rrect(BX - 6, BY - 6, BW + 12, BH + 12, 20, A, stroke=6)
            tag("✓ Boxart" if bs == "ok" else "Vorschau", BX + 12, BY + 12, bs == "ok")
        else:
            empty(BX, BY, BW, BH, "Boxart")

        # Name und System
        size = 40
        while size > 24 and P.width(self.title, size, bold=True, raw=True) > 820:
            size -= 2                        # lange Namen verkleinern statt abschneiden
        P.clip(415, 430, 820, 70)
        P.text(self.title, size, 415, 480, "ffffff", bold=True, raw=True)
        P.unclip()
        P.text(self.system["name"] if self.system else "", 24, 415, 522, "bdbdbd", raw=True)

        # Cartridge unter dem Namen
        cp, cs = slot("cartridge")
        CX, CY, CS = 415, 560, 240
        if cp and cp != "…":
            self.fit(P, cp, CX, CY, CS, CS)
            if cs == "pv":
                P.rrect(CX - 6, CY - 6, CS + 12, CS + 12, 20, A, stroke=6)
            tag("✓ Cartridge" if cs == "ok" else "Vorschau", CX + 10, CY + 10, cs == "ok")
        else:
            empty(CX, CY, CS, CS, "Cartridge")

        # Übersicht rechts
        y = 600
        for kind, label in KINDS:
            items = self.cands.get(kind) or []
            if kind in self.chosen:
                state = "✓ übernommen"
            elif kind == cur_kind and items:
                state = f"Vorschau {self.idx[kind] + 1} / {len(items)}"
            else:
                state = "– fehlt" if items else "– keine Bilder"
            w = P.text(label, 24, 700, y, "ffffff", bold=True, raw=True)
            P.text("  " + state, 24, 700 + w, y, "bdbdbd", raw=True)
            y += 46
        if self.chosen:
            P.hint([("Start", "Speichern")], 24, 700, y + 30, "bdbdbd", "ffffff")
        P.hint([("L3", "Großansicht")], 18, 1225, 925, "8a8a8a", "bdbdbd", align="r")


# ------------------------------------------------------------------ main ----

def main():
    log("RetroDualStation Artwork Manager", VERSION)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    a = App()

    def on_touch(kind, x, y):
        {"down": a.touch_down, "move": a.touch_move}.get(kind, lambda *_: a.touch_up())(x, y)
        a.dirty = True

    ui = Overlay(a.draw, on_touch)
    ui.show("artwork")
    ui.show_top(a.draw_top)
    if a.view == "start":
        a.start()

    joy = open_event(JOYPAD_NAME)
    home = open_event(HOME_NAME)
    tfd = open_event(TOUCH_NAME)
    touch = TouchReader(tfd, a.cfg) if tfd is not None else None
    grabbed = [fd for fd in (joy, home, tfd) if fd is not None]
    for fd in grabbed:
        grab(fd, True)          # Eingaben gehören nur dem Manager (ES und Kontrollcenter ruhen)
    kbd_open = [False]
    try:
        while not a.quit:
            fds = [fd for fd in grabbed]
            busy = a.busy or a.saving or any(v == "…" for v in a.previews.values()) or (a.kbd and a.kbd.hold)
            for fd in ui.pump(0.1 if busy else 0.5, fds):
                try:
                    if fd == tfd:
                        for ev in read_events(fd, (EV_SYN, EV_KEY, EV_ABS)):
                            t = touch.feed(*ev)
                            if t and ui.size:
                                on_touch(t[0], *touch.to_surface(t[1], t[2], *ui.size))
                        continue
                    for typ, code, value in read_events(fd):
                        if fd == home and typ == EV_KEY and code == BTN_Z and value == 1:
                            a.quit = True                         # Home: Manager beenden
                            continue
                        if a.kbd:
                            if typ == EV_KEY and code == BTN_EAST:
                                (a.kbd.a_down if value == 1 else a.kbd.a_up)() if value in (0, 1) else None
                            elif typ == EV_KEY and value == 1:
                                if code in DPAD:
                                    a.kbd.nav(*DPAD[code])
                                elif code == BTN_SOUTH:
                                    a.kbd.back()
                                elif code == BTN_TL:
                                    a.kbd.toggle_shift()
                                elif code == BTN_TR:
                                    a.kbd.toggle_layer()
                                elif code == BTN_START:
                                    a.kbd.ok()
                            elif typ == EV_ABS and code in (ABS_HAT0X, ABS_HAT0Y) and value:
                                d = 1 if value > 0 else -1
                                a.kbd.nav(d, 0) if code == ABS_HAT0X else a.kbd.nav(0, d)
                            a.dirty = True
                            continue
                        if typ == EV_ABS and code in (ABS_HAT0X, ABS_HAT0Y) and value:
                            d = 1 if value > 0 else -1
                            a.on_dir(d, 0) if code == ABS_HAT0X else a.on_dir(0, d)
                        elif typ == EV_KEY and value == 1:
                            if code in DPAD:
                                a.on_dir(*DPAD[code])
                            else:
                                a.on_key(code)
                        else:
                            continue
                        a.dirty = True
                except Exception:
                    log("Fehler (läuft weiter):\n" + traceback.format_exc().rstrip())
                    a.dirty = True
            if a.kbd and a.kbd.tick():
                a.dirty = True
            if a.saving and a.saving.get("done") and time.monotonic() > a.saving_until:
                a.saving = None
                a.dirty = a.top_dirty = True
                if a.after_saving:
                    nxt, a.after_saving = a.after_saving, None
                    nxt()
            if a.pending and not a.busy:
                nxt, a.pending = a.pending, None
                nxt()
            if a.message and time.monotonic() - a.message[1] > 4:
                a.message = None
                a.dirty = True
            if a.busy or a.saving or a.dirty:
                a.dirty = False
                ui.redraw()
            if (a.kbd is not None) != kbd_open[0]:   # Tastatur auf/zu → oberen Bildschirm umschalten
                kbd_open[0] = a.kbd is not None
                a.top_dirty = True
            if a.top_dirty:
                a.top_dirty = False
                ui.redraw_top()
    except KeyboardInterrupt:
        pass
    finally:
        for fd in grabbed:
            grab(fd, False)
        try:
            ui.hide_top()
            ui.hide()
        except Exception:
            pass
        if a.changed:   # EmulationStation zeigt die neuen Artworks nach dem Neuladen
            subprocess.run(["curl", "-fsS", "--max-time", "5", "http://localhost:1234/reloadgames"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("beendet")


if __name__ == "__main__":
    main()
