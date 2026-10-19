# To-do – ROCKNIX DualStation & Artwork Manager

Stand: 19.10.2026 · Eine Liste für alles, damit nichts verloren geht.

> **Leitsatz:** ROCKNIX DualStation – one system, two screens, everything in sync.
>
> Vision: ein Ökosystem aus Emulation, Gaming, Artwork-Manager, Scraping und
> Achievements, das am Gerät und am PC ineinandergreift. Der Leitsatz kommt auf
> die GitHub-Seite, sobald Kontrollcenter und Desktop-Begleiter da sind.

Neue Ideen kommen erst hier rein, dann wird entschieden, wann sie dran sind.

## Als Nächstes
- [ ] Bestandsaufnahme auf dem RG DS Plus (Befehle in [KONTROLLCENTER.md](KONTROLLCENTER.md))
- [ ] Artwork Manager: Baustellen sammeln (Stichpunkte vom Nutzer) und der Reihe nach beheben – **Grundlage vor allen Erweiterungen**

## ROCKNIX DualStation

### Kontrollcenter & Co. (Details: [KONTROLLCENTER.md](KONTROLLCENTER.md))
- [ ] Etappe 1: Schnelleinstellungen, Wisch-Gerüst, Anbernic-Taste, Pause, Hell/Dunkel, Akzentfarbe
- [ ] Etappe 2: Seite „Spiel“ (Buttons, Spickzettel, Tastenkürzel standardmäßig aus)
- [ ] Etappe 3: RetroAchievements
- [ ] Etappe 4: RetroArch-Touchmenü ersetzen, in den Installer
- [ ] Etappe 5: Gameswitcher (Return/Home-Taste, Auto-Speichern/Laden)
- [ ] DraStic testen: Auto-Speichern/Laden, Tastaturtasten als Kürzel
- [ ] DraStic: großes Pausemenü vom RG DS übernehmen (`librgdsmenu.so`)
- [ ] DraStic: eigene Einstellungsoberfläche (`drastic.cfg`)

### Themes & Geräte
- [ ] dii-ess-aye: eigene Ansichten wie bei canvas-ds
- [ ] Version für das normale RG DS (640×480)
- [ ] optional: ES-Patch für die Option „Standard-Rastergröße“

### Scraper
- [ ] ScreenScraper-Entwicklerzugang beantragen (Forum; Antragstext vorbereiten)
- [ ] mit Zugang: Scraper im Dual-Build von ES wieder aktivieren (Zugangsdaten nur als GitHub-Secret beim Bauen, nie im Repository)

## Artwork Manager

### Grundlage
- [ ] Baustellen beheben (siehe oben)
- [ ] Titelsuche verbessern, pro System der passende Weg:

  | System | Weg |
  |---|---|
  | DS/DSi, GBA | Seriennummer (Code gleich, letzter Buchstabe = Region) |
  | SNES | Seriennummer, Name als Rückfall |
  | GB/GBC | Seriennummer wo vorhanden, sonst Name |
  | NES, Master System, Mega Drive, PS1 | bereinigter Name + Ähnlichkeitswertung + Aliase |
  | CPS1–3 | Arcade-Datenbank (Hauptversion) |

  Reihenfolge: Seriennummer/Hauptversion → Name mit Wertung → Alias-Datei → manuelle Auswahl.
  Mit ScreenScraper-Zugang: Erkennung per Prüfsumme und Namen pro Region – ersetzt das meiste davon.
- [ ] Desktop-Starter: Update kam einmal nicht automatisch an – prüfen

### Ausbau
- [ ] gamelist.xml: Namen/Beschreibung/Daten bearbeiten, fehlende Spiele anlegen, verwaiste Einträge aufräumen
- [ ] Logos übertragen (DualStation: `romname-logo.png` → `<marquee>`)
- [ ] Metadaten (Beschreibung, Genre, Spieler, Jahr, Entwickler): ScreenScraper bevorzugt, sonst TheGamesDB/IGDB
- [ ] optional: Speicherplatz sparen (PNG-Farbreduktion, alte Scraper-Bilder verkleinern)
- [ ] Umbenennung überlegen (z. B. DualStation Studio / Companion), Hinweis „funktioniert auch mit ROCKNIXDS“
- [ ] Aufräumen: Branch `geraeteprofile` (v4.11.0) wird nicht genutzt

## Erledigt (Auszug)
- [x] v9: canvas-ds-Ansichten (Gamecarousel, Detailliert, Raster, Showcase, Spotlight), Links/Rechts im Dual-Modus, README mit Screenshots
- [x] Artwork Manager v5: Profil DualStation (`-hero` / `-icon` / `-box`), auf dem Gerät getestet
- [x] Kontrollcenter und Gameswitcher: Entwurf freigegeben
