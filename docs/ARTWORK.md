# RetroDualStation artwork standard

*[Deutsche Fassung](ARTWORK.de.md)*

Which images RetroDualStation expects per game – independent of any theme.
Any dual-screen theme can rely on these names and `gamelist.xml` tags; the Artwork Manager
(on the device and on a PC) writes exactly this.

## Files

Location: `/storage/roms/<system>/images/`, named after the ROM file without extension (`<rom>`).

| Type | File | gamelist.xml tag | Shape | Typical use |
|---|---|---|---|---|
| **Hero** | `<rom>-hero.png` | `<image>` | wide (≈ 3:1 to 16:9) | top screen background |
| **Boxart** | `<rom>-box.png` | `<boxart>` | 2:3 portrait | cover, grid |
| **Icon** | `<rom>-icon.png` | `<cartridge>` **and** `<thumbnail>` | 1:1, 1024 px, optional iiSU border | carousel, lists |
| Logo | from the scraper | `<marquee>` | transparent | title on top of the hero |
| Video | from the scraper | `<video>` | – | optional, top screen |

Paths in `gamelist.xml` are relative: `./images/<rom>-hero.png`.

## Rules

- The suffixes `-hero`, `-box` and `-icon` are **never written by the ES scraper**, so scraping
  does not overwrite them. Logo and video stay scraper media.
- `<thumbnail>` also points to the icon, so themes that only know `thumbnail` show it too.
- Every image is optional. Themes should fall back to scraper media when a file is missing
  (e.g. hero → `<image>` from the scraper, icon → `<thumbnail>`).
- Multi-disc games: one `.m3u` entry carries the artwork; the single discs are hidden.

## In a theme

ES theme variables: `{game:image}` (hero), `{game:boxart}`, `{game:cartridge}` (icon),
`{game:thumbnail}`, `{game:marquee}` – or the classic `md_image`, `md_thumbnail`, `md_marquee`.
canvas-ds is the reference: [theme/canvas-rds-overlay](../theme/canvas-rds-overlay).
