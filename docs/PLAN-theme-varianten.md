# Plan: Theme-Varianten (canvas-ds, später dii-ess-aye)

Stand: 17.10.2026 – Konzept, noch nicht umgesetzt.

Die Ansichten der Original-Themes werden durch diese Varianten ersetzt.
Auswahl über eine Theme-Einstellung (z. B. „Game list layout“).
Vor der Veröffentlichung bekommen beebono und toniremi Screenshots.

## Oberer Screen (alle Varianten)

Hero-Artwork (`image`), nach 5 Sekunden blendet das Video ein
(falls vorhanden). Ohne Video bleibt das Artwork stehen.

## Unterer Screen

| # | Variante | Inhalt | Medien |
|---|---|---|---|
| I | Simple 3 | horizontales Karussell, 3 Icons (wie Systemkarussell) | Icon → `thumbnail` |
| II | Simple 5 | horizontales Karussell, 5 Icons in einer Reihe | Icon → `thumbnail` |
| III | Details | links senkrechtes Cover-Karussell (ein Cover groß, vorheriges/nächstes oben und unten angedeutet), rechts Spielbeschreibung als scrollender Text, darunter Spieleranzahl, Veröffentlichung, Entwickler | Grid → `boxart` |
| IV | Logos | senkrechtes Karussell (oben ↔ unten wie Original-canvas), aber gerade und mittig; ausgewähltes Logo groß | Logo → `marquee` |
| V | Raster | Cover im Raster (Grid 2:3) | Grid → `boxart` |
| VI | Liste | Textliste, Namen mittig zentriert, kleines Icon beim ausgewählten Spiel | optional |

Vorbild für I: Test-Zweig `artwork-ansicht`
(`theme/canvas-ds-rgds-plus-overlay/_inc/game-carousel/carousel-art.xml`):
oberes Bild 0.44 breit, runde Ecken wie die Icons.

Schematische Vorschau: `docs/vorschau-varianten.png` (17.10.2026, vom Nutzer für gut befunden).

## Artwork Manager anpassen

- Logos als `marquee` schreiben; `marquee` nicht mehr aus der gamelist.xml löschen
  (`update_gamelist_media` entfernt es bisher).
- Zielgrößen je Gerät: RG DS Plus Icon 512 × 512, Grid 400 × 600, Hero ≤ 1024 × 768;
  RG DS Icon 320 × 320, Grid 240 × 360, Hero ≤ 640 × 480.
- Theme-Patch (ROCKNIXDS-Theme) für diese Themes nicht mehr nötig.

## Danach

- dii-ess-aye-rgds-plus an die Varianten angleichen.
- Version für das normale RG DS (640 × 480 pro Screen).
