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
                    BTN_MODE, BTN_Z, JOYPAD_NAME, HOME_NAME, TOUCH_NAME, PI)
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
KINDS = [("boxart", "Boxart"), ("cartridge", "Cartridge / Icon"), ("image", "Image")]
ROWS = 8            # sichtbare Zeilen in Listen


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
        self.results = []                             # Trefferliste der Suche
        self.query = ""

    # -- Hilfen --
    def say(self, text):
        self.message = (text, time.monotonic())
        self.dirty = True

    def work(self, label, fn):
        """fn im Hintergrund ausführen; Fehler werden angezeigt statt abzubrechen."""
        if self.busy:
            return
        self.busy = label
        self.dirty = True

        def run():
            try:
                fn()
            except Exception as exc:
                log("Fehler:\n" + traceback.format_exc().rstrip())
                self.say(f"Fehler: {exc}")
            finally:
                self.busy = None
                self.dirty = self.top_dirty = True
        threading.Thread(target=run, daemon=True).start()

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

    def open_system(self, i):
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
        self.work(f"{s['name']} wird geladen …", go)

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
            self.cands = artwork_candidates_for_games(result, pages, sgdb)
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
        """Aktuellen Kandidaten und Nachbarn im Hintergrund laden."""
        kind = self.kind_key()
        items = self.cands.get(kind) or []
        i = self.idx[kind]
        for j in (i, i + 1, i - 1):
            if 0 <= j < len(items):
                self._load_preview(items[j])

    def _load_preview(self, item):
        url = item.get("preview_url") or item.get("thumb") or item.get("url")
        if not url or url in self.previews:
            return
        self.previews[url] = "…"

        def go():
            try:
                data = cached_download(WORK / "data" / "cache", url, download_artwork)
                path = PREVIEW_DIR / "cand" / (str(abs(hash(url))) + ".png")
                to_png(data, path)
                self.previews[url] = str(path)
            except Exception as exc:
                log("Vorschau nicht ladbar:", url, exc)
                self.previews[url] = None
            self.top_dirty = self.dirty = True
        threading.Thread(target=go, daemon=True).start()

    def preview_of(self, item):
        if not item:
            return None
        return self.previews.get(item.get("preview_url") or item.get("thumb") or item.get("url"))

    def step(self, d):
        kind = self.kind_key()
        n = len(self.cands.get(kind) or [])
        if n:
            self.idx[kind] = (self.idx[kind] + d) % n
            self.want_previews()
            self.top_dirty = True

    def switch_kind(self, d):
        self.kind = (self.kind + d) % len(KINDS)
        self.want_previews()
        self.top_dirty = True

    def toggle_choice(self):
        kind, c = self.kind_key(), self.cand()
        if not c:
            return
        if self.chosen.get(kind) is c:
            del self.chosen[kind]
        else:
            self.chosen[kind] = c
        self.top_dirty = True

    def transfer(self):
        if not self.chosen:
            self.say("Erst mit A ein Artwork auswählen")
            return
        rom, chosen, system = self.rom, dict(self.chosen), self.system["key"]

        def go():
            if self.settings.get("backup") and system not in self.backed_up:
                self.busy = "Sicherung wird erstellt …"
                self.dirty = True
                b = self.app.backup_artwork()
                self.backed_up.add(system)
                log("Sicherung:", b.get("path"))
            self.busy = "Artwork wird vorbereitet …"
            self.dirty = True
            self.app.stage_scraper_artwork(rom, chosen,
                                           lambda url: cached_download(WORK / "data" / "cache", url, download_artwork))
            preview = self.app.preview()
            media = preview.get("media") or []
            if not media or (preview.get("set") or {}).get("rom") != rom or (preview.get("xml") or {}).get("games_changed") != 1:
                raise RuntimeError("Sicherheitsprüfung fehlgeschlagen – nichts geschrieben")
            self.busy = "Artwork wird gespeichert …"
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
            self.say(f"{n} Artwork(s) gespeichert")
        self.work("Wird gespeichert …", go)

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
            self.results = manual_search_rows(text, iidb_request, sgdb_request(api) if api else None)
            self.view, self.sel, self.scroll = "search", 0, 0
            if not self.results:
                self.say("Keine Treffer – anderen Namen probieren")
        self.work("Suche läuft …", go)

    def pick_result(self, i):
        row = self.results[i]
        forced = {"iidb" if row["source"] == "iiDB" else "steamgriddb": row["item"]}
        gi = next((n for n, g in enumerate(self.games) if g[0] == self.rom), 0)
        self.open_game(gi, forced=forced, name=row["name"])

    def edit_key(self):
        def done(text=None):
            value = (text if isinstance(text, str) else self.kbd.text if self.kbd else "").strip()
            self.kbd = None
            write_cfg_key(value)
            self.say("SteamGridDB-Key gespeichert" if value else "SteamGridDB-Key entfernt")
        self.kbd = Keyboard(self, "SteamGridDB API-Key", done, secret=True)

    # -- Bedienung --
    def list_len(self):
        return {"systems": len(self.systems) + 1, "games": len(self.games),
                "search": len(self.results)}.get(self.view, 0)

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
            if i == len(self.systems):
                self.edit_key()
            elif self.systems:
                self.open_system(i)
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
        if self.view == "search":
            self.view = "game"
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

    def on_key(self, code):
        if self.view == "setup":
            if code == BTN_EAST:
                self.answer_setup(True)
            elif code == BTN_SOUTH:
                self.answer_setup(False)
            return
        if code == BTN_SOUTH:
            self.back()
            return
        if self.busy:
            return
        if self.view == "game":
            {BTN_EAST: self.toggle_choice, BTN_NORTH: self.transfer, BTN_WEST: self.open_search,
             BTN_START: self.transfer,
             BTN_TL: lambda: self.switch_kind(-1), BTN_TR: lambda: self.switch_kind(1)}.get(code, lambda: None)()
        elif code == BTN_EAST:
            self.activate()
        elif code in (BTN_TL, BTN_TR):
            self.move(-ROWS if code == BTN_TL else ROWS)

    def on_dir(self, dx, dy):
        if self.view == "game":
            if dx:
                self.step(dx)
            elif dy:
                self.switch_kind(dy)
        elif dy:
            self.move(dy)

    def on_tap(self, x, y):
        hit = self._hit(x, y)
        if not hit:
            return
        kind, val = hit
        if kind == "row":
            if self.sel == val:
                self.activate(val)
            else:
                self.sel = val
        elif kind == "setup":
            self.answer_setup(val)
        elif kind == "btn":
            {"back": self.back, "choose": self.toggle_choice, "save": self.transfer,
             "search": self.open_search, "prev": lambda: self.step(-1), "next": lambda: self.step(1),
             "up": lambda: self.move(-ROWS), "down": lambda: self.move(ROWS)}.get(val, lambda: None)()
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
        dy = y1 - y0
        if abs(dy) > 60 and self.view in ("games", "search", "systems"):   # wischen = blättern
            self.move(-round(dy / 85))
            return
        if self.view == "game" and abs(x1 - x0) > 80 and abs(dy) < 60:   # wischen = Kandidat
            self.step(-1 if x1 > x0 else 1)
            return
        self.on_tap(x0, y0)

    # ---------------------------------------------------------- Zeichnen ----
    def button(self, P, x, y, w, label, action, primary=False, key=None):
        T, A = self.T, self.accent
        P.rrect(x, y, w, 78, 22, A if primary else T["tile"])
        txt = (f"{key}  " if key else "") + label
        P.text(txt, 28, x + w / 2, y + 50, "ffffff" if primary else T["text"], bold=True, align="c", raw=True)
        self.hits.append((x, y, w, 78, ("btn", action)))

    def header(self, P, title, sub=None):
        T = self.T
        P.text(title, 44, 50, 85, T["text"], bold=True, raw=True)
        if sub:
            P.text(sub, 26, 50, 125, T["muted"], raw=True)

    def draw(self, cr, w, h, _view):
        P = self.pen = Pen(cr, w, h)
        T = self.T
        P.fill_all(T["bg"])
        self.hits = []
        if self.kbd:
            self.kbd.draw(P)
            return
        if self.view == "setup":
            self.draw_setup(P)
        elif self.view in ("systems", "games", "search"):
            self.draw_list(P)
        elif self.view == "game":
            self.draw_game(P)
        else:
            self.header(P, "Artwork Manager")
        busy, message = self.busy, self.message   # Hintergrund-Threads ändern das jederzeit
        if busy:
            P.rrect(230, 400, 800, 150, 30, T["card"])
            P.text(str(busy), 32, 630, 488, T["text"], bold=True, align="c", raw=True)
        elif message and time.monotonic() - message[1] < 4:
            P.rrect(130, 800, 1000, 90, 26, T["card"])
            P.text(str(message[0]), 28, 630, 856, T["text"], align="c", raw=True)

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

    def draw_list(self, P):
        T, A = self.T, self.accent
        if self.view == "systems":
            self.header(P, "Artwork Manager", "System wählen")
            rows = [(s["name"], f"{s['rom_count']} Spiele", None) for s in self.systems]
            key = "gesetzt" if steamgriddb_key() else "fehlt"
            rows.append(("SteamGridDB API-Key", key, None))
        elif self.view == "games":
            self.header(P, self.system["name"], f"{len(self.games)} Spiele · Ampel: vorhandene Artworks")
            rows = [(name, None, st) for _rom, name, st in self.games]
        else:
            self.header(P, "Suchergebnisse", f"„{self.query}“ · Spiel wählen")
            rows = [(r["name"], f"{r['console']} · {r['year']} · {r['source']}", None) for r in self.results]
        y0, rh = 160, 78
        for n in range(self.scroll, min(len(rows), self.scroll + ROWS)):
            name, right, st = rows[n]
            y = y0 + (n - self.scroll) * rh
            focus = n == self.sel
            P.rrect(40, y, 1180, rh - 8, 20, T["focus"] if focus else T["card"])
            if focus:
                P.rrect(40, y, 8, rh - 8, 4, A)
            x = 70
            if st is not None:
                col = {0: "e5383b", 1: "f08c00", 2: "f08c00"}.get(st, "2bb673")
                P.circle(85, y + (rh - 8) / 2, 12, col)
                x = 115
            P.clip(x, y, 1180 - x - (330 if right else 20), rh)
            P.text(name, 30, x, y + 47, T["text"], bold=focus, raw=True)
            P.unclip()
            if right:
                P.text(right, 24, 1195, y + 46, T["muted"], align="r", raw=True)
            self.hits.append((40, y, 1180, rh - 8, ("row", n)))
        if not rows:
            P.text("Nichts gefunden", 30, 630, 400, T["muted"], align="c", raw=True)
        if len(rows) > ROWS:
            P.text(f"{self.sel + 1}/{len(rows)}", 24, 1220, 125, T["muted"], align="r", raw=True)
        self.button(P, 40, 840, 280, "Zurück" if self.view != "systems" else "Beenden", "back", key="B")
        if len(rows) > ROWS:
            self.button(P, 680, 840, 260, "Seite hoch", "up", key="L")
            self.button(P, 960, 840, 260, "Seite runter", "down", key="R")

    def draw_game(self, P):
        T, A = self.T, self.accent
        self.header(P, self.title, self.system["name"])
        x = 40
        for n, (kind, label) in enumerate(KINDS):
            cnt = len(self.cands.get(kind) or [])
            on = n == self.kind
            w = 380
            P.rrect(x, 160, w, 90, 24, A if on else T["tile"])
            tick = "✓ " if kind in self.chosen else ""
            P.text(f"{tick}{label}", 28, x + w / 2, 202, "ffffff" if on else T["text"], bold=True, align="c", raw=True)
            P.text(f"{cnt} Kandidaten", 22, x + w / 2, 235, "ffffff" if on else T["muted"], align="c", raw=True)
            self.hits.append((x, 160, w, 90, ("kind", n)))
            x += w + 20
        kind = self.kind_key()
        items = self.cands.get(kind) or []
        P.rrect(40, 280, 1180, 300, 28, T["card"])
        if items:
            c = items[self.idx[kind]]
            P.text(f"Kandidat {self.idx[kind] + 1} von {len(items)}", 34, 630, 350, T["text"], bold=True, align="c", raw=True)
            P.text(str(c.get("source") or ""), 26, 630, 395, T["muted"], align="c", raw=True)
            chosen = self.chosen.get(kind) is c
            P.text("✓ ausgewählt" if chosen else "A = auswählen", 28, 630, 450, A if chosen else T["muted"],
                   bold=chosen, align="c", raw=True)
            P.text(f"Ausgewählt: {len(self.chosen)} von 3 Arten", 24, 630, 530, T["muted"], align="c", raw=True)
            self.button(P, 60, 450, 140, "◀", "prev")
            self.button(P, 1060, 450, 140, "▶", "next")
        else:
            P.text("Keine Kandidaten für diese Art", 30, 630, 440, T["muted"], align="c", raw=True)
        self.button(P, 40, 620, 370, "Auswählen", "choose", key="A")
        self.button(P, 445, 620, 370, "Spiel suchen", "search", key="Y")
        self.button(P, 850, 620, 370, "Speichern", "save", primary=bool(self.chosen), key="X")
        self.button(P, 40, 840, 280, "Zurück", "back", key="B")
        P.text("◀ ▶ blättern · L / R Art wechseln", 24, 1220, 890, T["muted"], align="r", raw=True)

    # oberer Bildschirm
    def fit(self, P, path, x, y, w, h):
        """Bild vollständig einpassen (nicht beschneiden)."""
        try:
            img = Image.open(path)
            iw, ih = img.size
        except Exception:
            return False
        k = min(w / iw, h / ih)
        dw, dh = iw * k, ih * k
        return P.image(path, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, r=12, stretch=True)

    def draw_top(self, cr, w, h):
        P = Pen(cr, w, h)
        T, A = self.T, self.accent
        P.fill_all("000000")
        if self.view != "game" or not self.rom:
            P.text("Artwork Manager", 64, 630, 430, "ffffff", bold=True, align="c", raw=True)
            P.text("RetroDualStation", 32, 630, 490, "bdbdbd", align="c", raw=True)
            return
        kind = self.kind_key()
        label = KINDS[self.kind][1]
        c = self.cand()
        path = self.preview_of(c)
        if path and path != "…":
            self.fit(P, path, 40, 70, 860, 840)
        elif c:
            P.text("Lädt …" if path == "…" else "Vorschau nicht verfügbar", 34, 470, 480, "bdbdbd",
                   align="c", raw=True)
        else:
            P.text("Keine Kandidaten", 34, 470, 480, "bdbdbd", align="c", raw=True)
        if c and self.chosen.get(kind) is c:
            P.rrect(40, 70, 860, 840, 16, A, stroke=6)
        P.text(label, 34, 40, 50, "ffffff", bold=True, raw=True)
        # rechts: vorhandenes Artwork zum Vergleich
        P.text("Aktuell", 28, 1080, 110, "bdbdbd", align="c", raw=True)
        cur = self.current.get(kind)
        P.rrect(940, 130, 280, 280, 16, "262626")
        if not (cur and self.fit(P, cur, 950, 140, 260, 260)):
            P.text("keins", 26, 1080, 280, "8a8a8a", align="c", raw=True)
        if c:
            P.text(f"{self.idx[kind] + 1} / {len(self.cands.get(kind) or [])}", 30, 1080, 480, "ffffff",
                   bold=True, align="c", raw=True)


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
    try:
        while not a.quit:
            fds = [fd for fd in grabbed]
            busy = a.busy or any(v == "…" for v in a.previews.values()) or (a.kbd and a.kbd.hold)
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
            if a.message and time.monotonic() - a.message[1] > 4:
                a.message = None
                a.dirty = True
            if a.busy or a.dirty:
                a.dirty = False
                ui.redraw()
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
