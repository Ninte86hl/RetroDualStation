# canvas-ds-rgds-plus – Ansichten und Artworks

Stand: 18.10.2026 (Zweig `theme-varianten`)

| Eintrag in ES | Unterer Screen: Anordnung | Artwork | Datei | gamelist-Eintrag |
|---|---|---|---|---|
| **Alle (oberer Screen)** | Hero mittig auf Höhe der Icons, runde Ecken, nach 5 s Video, darunter das Systemlogo | Hero | `romname-hero.png` | `image` |
| **Detailliert** | Spielnamen als Liste mittig, ausgewähltes Spiel hervorgehoben | – | – | – |
| **Automatisch / Gamecarousel** | 3 Icons nebeneinander, das mittlere größer, darunter der Name des ausgewählten Spiels | Icon | `romname-icon.png` | `cartridge` + `thumbnail` |
| **Spotlight** | Karussell wie die Systemansicht, seitlich einblendend: jede Karte links Grid (2:3), rechts Logo; ausgewählte Karte mittig und größer, Nachbarn halb am Rand | Grid + Logo | `romname-box.png` + `romname-logo.png` | `boxart` + `marquee` |
| **Showcase** | links senkrechtes Cover-Karussell (Nachbarn ragen oben und unten ins Bild), rechts Name, Beschreibung, Spieler, Jahr, Entwickler | Grid (2:3) | `romname-box.png` | `boxart` |
| **Oberer Screen, nach 5 s** | Video blendet über das Hero-Bild | Video | vom Scraper | `video` |

**Ersatzbilder:** Fehlt das Icon, zeigt das Karussell die ScreenScraper-Hülle aus
`thumbnail`. Fehlt das Grid, zeigen Showcase und Spotlight das Icon oder die Hülle;
fehlt das Logo, zeigt Spotlight den Spielnamen.

## Für den Artwork Manager

- Icon: `romname-icon.png`, Einträge `cartridge` **und** `thumbnail`
- Grid: `romname-box.png`, Eintrag `boxart` (gleicher Name wie ScreenScraper –
  ein Scrape mit Box-Art überschreibt ihn)
- Hero: `romname-hero.png`, Eintrag `image`
- Logo: `romname-logo.png`, Eintrag `marquee`; `marquee` nicht mehr löschen
- Zielgrößen: RG DS Plus Icon 512 × 512, Grid 400 × 600, Hero ≤ 1024 × 768;
  RG DS Icon 320 × 320, Grid 240 × 360, Hero ≤ 640 × 480
- Bestehende Geräte: `tools/migrate-artwork.py` (Icon → `-icon.png`,
  Hero → `-hero.png`; Grids bleiben)
