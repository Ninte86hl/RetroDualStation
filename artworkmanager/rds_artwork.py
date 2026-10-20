#!/usr/bin/env python3
"""RetroDualStation Artwork Manager – die Gerätefassung des RocknixDS Artwork Managers.

Oberer Bildschirm: großes Artwork (Kandidat) zum Vergleichen.
Unterer Bildschirm: System, Spieleliste, Suche und Bedienung (Touch + Tasten).

Such-, Erkennungs- und Schreiblogik kommen unverändert aus dem Paket
rocknixds_artwork_manager; nur der Gerätezugriff läuft lokal statt über SSH.
Zeichnen, Bildschirme, Eingabe und Bildschirmtastatur kommen vom Kontrollcenter.
"""
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
            for rom in self.app.roms():
                base = Path(str(rom)).name
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
        self.view, self.rom = "games", None
        self.scroll = max(0, min(self.scroll, self.sel), self.sel - ROWS + 1)
        self.top_dirty = True

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

    def open_game(self, i, forced=None, name=None):
        rom, title, _st = self.games[i]
        self.rom, self.title = rom, title
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
        self.work("Artworks werden gesucht …", go)

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
                    data = cached_download(WORK / "data" / "cache", url, download_artwork)
                    path = PREVIEW_DIR / "cand" / (str(abs(hash(url))) + ".png")
                    size = to_png(data, path)
                    self.previews[url] = str(path)
                    if item in (self.cands.get("boxart") or []) and is_2x3(*size) is False:
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
            self.app.stage_scraper_artwork(rom, chosen,
                                           lambda url: cached_download(WORK / "data" / "cache", url, download_artwork))
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
            self.saving_until = time.monotonic() + 1.2      # kurz „Gespeichert“ zeigen

        def run():
            try:
                go()
            except Exception:
                self.saving = None
                raise
        self.work("saving", run)

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
        return {"systems": len(self.systems), "games": len(self.games), "search": len(self.results),
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
            if self.systems:
                self.open_system(i)
        elif self.view == "settings":
            rows = self.setting_rows()
            if 0 <= i < len(rows):
                rows[i][2]()
        elif self.view == "gsearch" and self.gresults:
            self.pick_global(i)
        elif self.view == "restore" and self.backups:
            self.ask_restore(i)
        elif self.view == "games" and self.games:
            self.open_game(i)
        elif self.view == "search" and self.results:
            self.pick_result(i)

    def back(self):
        if self.kbd:
            self.kbd.back()
            return
        if self.busy:
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
            self.view, self.sel, self.scroll = "settings", 2, 0
        elif self.view == "game":
            self.sel = next((n for n, g in enumerate(self.games) if g[0] == self.rom), self.sel)
            self.scroll = max(0, min(self.scroll, self.sel), self.sel - ROWS + 1)
            self.view, self.rom = "games", None
        elif self.view == "games":
            self.view = "systems"
            self.sel = next((n for n, s in enumerate(self.systems) if s is self.system), 0)
            self.scroll = max(0, self.sel - ROWS + 1)
        else:
            self.quit = True
        self.top_dirty = True

    def buttons(self):
        """Belegung der festen A/B/X/Y-Leiste je Ansicht: (Taste, Text, Aktion | None)."""
        if self.view == "game":
            kind, c = self.kind_key(), self.cand()
            taken = c is not None and self.chosen.get(kind) is c
            return [("A", "Abwählen" if taken else "Übernehmen", self.toggle_choice if c else None),
                    ("B", "Batch beenden" if self.batch else "Zurück", self.back),
                    ("X", "Editor", None),          # vorgemerkt: 1:1-Bild mit iiSU-Rahmen

                    ("Y", "Spiel suchen", self.open_search)]
        a_label = {"systems": "Öffnen", "games": "Öffnen", "search": "Auswählen", "gsearch": "Öffnen",
                   "settings": "Ändern", "restore": "Wiederherstellen"}.get(self.view, "")
        return [("A", a_label, self.activate if self.list_len() else None),
                ("B⌂" if self.view == "systems" else "B", "Beenden" if self.view == "systems" else "Zurück", self.back),
                ("X", "Einstellungen", self.open_settings) if self.view == "systems" else ("X", "", None),
                ("Y", "Spiel suchen", self.open_global_search) if self.view == "systems" else ("Y", "", None)]

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

        def then():
            gi = next((n for n, g in enumerate(self.games) if g[0].casefold() == h["rom"].casefold()), None)
            if gi is None:
                self.say("Spiel in diesem System nicht gefunden")
                return
            self.sel = gi
            self.scroll = max(0, gi - ROWS + 1)
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
            ("Sicherung wiederherstellen", f"{len(backups)} vorhanden", self.open_restore),
            ("Sicherungen aufräumen", f"{len(backups)} · {human(sum(b.stat().st_size for b in backups))}",
             self.prune_backups),
            ("Zwischenspeicher leeren", human(cache), self.clear_cache),
            ("Log leeren", human(log_file.stat().st_size) if log_file.exists() else "–", self.clear_log),
        ]

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

    def clear_log(self):
        try:
            os.truncate(WORK / "manager.log", 0)
        except OSError:
            pass
        self.say("Log geleert")

    def on_key(self, code):
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
        elif code in (BTN_TL, BTN_TR):
            d = -1 if code == BTN_TL else 1
            self.switch_kind(d) if self.view == "game" else self.move(d * ROWS)
        elif code == BTN_START and self.view == "game":
            self.transfer()
        elif code == BTN_START and self.view == "systems" and self.systems:
            self.open_system(self.sel)                       # Einzelmodus
        elif code == BTN_SELECT and self.view == "systems" and self.systems:
            self.open_system(self.sel, batch=True)           # Batch
        elif code == BTN_SELECT and self.view == "game" and self.batch:
            self.batch_next(False)                           # Spiel überspringen

    def on_dir(self, dx, dy):
        if self.busy or self.confirm:
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
        """Kleines Haus für die Home-Taste (Dach + Körper)."""
        cr, sc = P.cr, P.s
        cc.cairo.cairo_new_path(cr)
        cc.cairo.cairo_move_to(cr, P.X(cx - 11), P.Y(cy - 1))
        cc.cairo.cairo_line_to(cr, P.X(cx), P.Y(cy - 11))
        cc.cairo.cairo_line_to(cr, P.X(cx + 11), P.Y(cy - 1))
        cc.cairo.cairo_close_path(cr)
        P.color(c)
        cc.cairo.cairo_fill(cr)
        P.rrect(cx - 7, cy - 2, 14, 12, 2, c)

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
        P = self.pen = Pen(cr, w, h)
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

    def draw_setup(self, P):
        T = self.T
        self.header(P, "Artwork Manager", "Einmalige Frage – gilt ab jetzt immer")
        P.rrect(50, 170, 1160, 380, 30, T["card"])
        lines = ["Vor dem ersten Speichern pro System automatisch eine",
                 "Sicherung anlegen (gamelist.xml und vorhandene Artworks)?",
                 "",
                 "Empfohlen. Die Sicherung liegt danach unter",
                 "/storage/roms/ports/artworkmanager/data/backups"]
        for n, line in enumerate(lines):
            P.text(line, 30, 90, 240 + n * 52, T["text"] if n < 2 else T["muted"], raw=True)
        P.rrect(50, 600, 560, 110, 30, self.accent)
        P.text("A  Ja, sichern", 34, 330, 668, "ffffff", bold=True, align="c", raw=True)
        self.hits.append((50, 600, 560, 110, ("setup", True)))
        P.rrect(650, 600, 560, 110, 30, T["tile"])
        P.text("B  Nein", 34, 930, 668, T["text"], bold=True, align="c", raw=True)
        self.hits.append((650, 600, 560, 110, ("setup", False)))

    def draw_view(self, P):
        """Die eigentliche Ansicht (ohne Tastatur, Ladebildschirm und Meldungen)."""
        if self.view == "setup":
            self.draw_setup(P)
        elif self.view in ("systems", "games", "search", "settings", "gsearch", "restore"):
            self.draw_list(P)
        elif self.view == "game":
            self.draw_game(P)
        else:
            self.header(P, "Artwork Manager")

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
            rows = [(s["name"], f"{s['rom_count']} Spiele", None) for s in self.systems]
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
            rows = [(name, None, st) for _rom, name, st in self.games]
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
        P = Pen(cr, w, h)
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
        if self.view not in ("game", "search") or not self.rom:
            P.text("Artwork Manager", 64, 630, 430, "ffffff", bold=True, align="c", raw=True)
            P.text("RetroDualStation", 32, 630, 490, "bdbdbd", align="c", raw=True)
            return
        kind = self.kind_key()
        c = self.cand()
        b = self.batch
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
