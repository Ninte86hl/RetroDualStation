# RetroDualStation-Artwork-Standard

*[English version](ARTWORK.md)*

Welche Bilder RetroDualStation pro Spiel erwartet – unabhängig vom Theme.
Jedes Dual-Screen-Theme kann sich auf diese Namen und `gamelist.xml`-Tags verlassen; der Artwork Manager
(am Gerät und am PC) schreibt genau das.

## Dateien

Ort: `/storage/roms/<system>/images/`, benannt nach der ROM-Datei ohne Endung (`<rom>`).

| Art | Datei | gamelist.xml-Tag | Form | Typische Nutzung |
|---|---|---|---|---|
| **Hero** | `<rom>-hero.png` | `<image>` | breit (≈ 3:1 bis 16:9) | Hintergrund oben |
| **Boxart** | `<rom>-box.png` | `<boxart>` | 2:3 hochkant | Cover, Raster |
| **Icon** | `<rom>-icon.png` | `<cartridge>` **und** `<thumbnail>` | 1:1, 1024 px, optional iiSU-Rahmen | Karussell, Listen |
| Logo | vom Scraper | `<marquee>` | transparent | Titel über dem Hero |
| Video | vom Scraper | `<video>` | – | optional, oben |

Pfade in der `gamelist.xml` sind relativ: `./images/<rom>-hero.png`.

## Regeln

- Die Endungen `-hero`, `-box` und `-icon` schreibt der ES-Scraper **nie** – Scrapen überschreibt
  sie also nicht. Logo und Video bleiben Scraper-Medien.
- `<thumbnail>` zeigt ebenfalls auf das Icon, damit Themes, die nur `thumbnail` kennen, es auch zeigen.
- Jedes Bild ist optional. Themes sollten bei fehlender Datei auf Scraper-Medien zurückfallen
  (z. B. Hero → `<image>` vom Scraper, Icon → `<thumbnail>`).
- Mehrteilige Spiele: Ein `.m3u`-Eintrag trägt die Artworks, die einzelnen Discs sind ausgeblendet.

## Im Theme

ES-Theme-Variablen: `{game:image}` (Hero), `{game:boxart}`, `{game:cartridge}` (Icon),
`{game:thumbnail}`, `{game:marquee}` – oder klassisch `md_image`, `md_thumbnail`, `md_marquee`.
Referenz ist canvas-ds: [theme/canvas-rds-overlay](../theme/canvas-rds-overlay).
