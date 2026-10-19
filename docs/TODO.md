# To-do – RetroDualStation & Artwork Manager

Stand: 19.10.2026 · Eine Liste für alles, damit nichts verloren geht.

> **Leitsatz:** RetroDualStation – one system, two screens, everything in sync.
>
> Vision: ein Ökosystem aus Emulation, Gaming, Artwork-Manager, Scraping und
> Achievements, das am Gerät und am PC ineinandergreift. Der Leitsatz kommt auf
> die GitHub-Seite, sobald Kontrollcenter und Desktop-Begleiter da sind.

Neue Ideen kommen erst hier rein, dann wird entschieden, wann sie dran sind.

## Als Nächstes
- [x] Bestandsaufnahme auf dem RG DS Plus (Ergebnis in [KONTROLLCENTER.md](KONTROLLCENTER.md))
- [x] Entscheidung (19.10.2026): Kontrollcenter als **Eigenentwicklung** (eigener Code, MIT wie der Rest; lowerdeck nur als Hinweis, dass der Weg funktioniert – kein Code übernommen)
- [ ] Artwork Manager: Baustellen sammeln (Stichpunkte vom Nutzer) und der Reihe nach beheben – **Grundlage vor allen Erweiterungen**

## RetroDualStation

### Umbenennung ROCKNIX DualStation → RetroDualStation (beschlossen 19.10.2026)
- [ ] GitHub-Repository umbenennen (z. B. `retrodualstation`; GitHub leitet alte Links weiter)
- [ ] README (EN/DE), CREDITS, Overlay-README, Doku: Name und Leitsatz
- [ ] Installer/Uninstaller, Ports-Einträge, Meldungen, Log-Namen; ZIP-Namen ab dem nächsten Release
- [ ] Ankündigung mit neuem Namen und Logo
- Easter Egg (bewusst nicht erklärt): RDS liest sich auch als **R**OCKNIX **D**ual**S**tation,
  Farben Rot (ROCKNIX) · Blau (JELOS) · Weiß – für Kenner der Szene ableitbar,
  die Basis wird in den Danksagungen genannt

### Kontrollcenter & Co. (Details: [KONTROLLCENTER.md](KONTROLLCENTER.md))
- [x] Etappe 1 (abgeschlossen 19.10.2026): Schnelleinstellungen, Seiten, Anbernic-Taste, Pause, Hell/Dunkel, Akzentfarbe, WLAN/Bluetooth-Untermenüs, Tastatur, externe Controller, Englisch, Autostart
- [ ] Etappe 2: Seite „Spiel“ (Buttons, Spickzettel, Tastenkürzel standardmäßig aus)
- [ ] Etappe 3: RetroAchievements
- [x] Etappe 4: RetroArch-Touchmenü (lowerdeck) ersetzt, CC im Installer (19.10.2026, Test der ZIP ausstehend)
- [ ] Etappe 5: Gameswitcher (Return/Home-Taste, Auto-Speichern/Laden)
- [ ] ES (eigener Dual-Build): Bluetooth-Menü (Gerät koppeln) erstreckt sich über beide Bildschirme – auf einen Bildschirm begrenzen (gefunden 19.10.2026)
- [ ] ES (eigener Dual-Build): `system.cfg` neu einlesen, wenn sie sich geändert hat (z. B. beim Öffnen des Menüs) – sonst zeigt das ES-Menü WLAN/Bluetooth nach dem Umschalten im Kontrollcenter erst nach ES-Neustart richtig an
- [x] Kontrollcenter: Pause in RetroArch, DraStic und DSperate getestet (19.10.2026)
- [ ] Kontrollcenter: Mini-Power-Menü wie bei Android – Ausschalten, Neustart, Ruhemodus,
      ES neu starten (mit Rückfrage; laufendes Spiel vorher speichern/beenden).
      Aufruf (entschieden 19.10.2026): **Ein/Aus-Taste kurz drücken**; Ruhemodus per Zuklappen
      (Hall-Sensor, bleibt bei ROCKNIX) oder über den ersten Knopf im Menü
- [ ] Kontrollcenter: Zuklappen/Aufklappen berücksichtigen (Pause bleibt bis zum Aufklappen;
      „Unterer Screen aus“ nach dem Aufklappen beibehalten bzw. bewusst wieder einschalten)
- [ ] Kontrollcenter: „Läuft gerade“ über die ES-Schnittstelle `http://localhost:1234/runningGame`
- [ ] Kontrollcenter: Log-Manager für einfache Fehlersuche – Logs von Kontrollcenter, ES,
      RetroArch, DraStic, System an einer Stelle ansehen; „Fehlerbericht erstellen“ packt sie
      in eine Datei (z. B. `/storage/logs/`), die man per Netzwerkfreigabe holen kann
- [ ] Kontrollcenter: „Als Spieler 1 verwenden“ für Controller im Bluetooth-Untermenü
      (ES übergibt die Zuordnung per `--controllers` an runemu → setsettings →
      `input_playerN_joypad_index`, wirkt nur bei RetroArch; DraStic/DSperate prüfen)
- [ ] Kontrollcenter: Koppeln während eines Spiels – runemu beendet `rocknix-bluetooth-agent`
      beim Spielstart; CC muss den Helfer bei Bedarf selbst starten (`systemd-run rocknix-bluetooth-agent`)
- [ ] Kontrollcenter: RetroArch-Touchflächen (Savestates etc.) auf dem unteren Screen bei „Screen aus“ prüfen – evtl. abschalten
- [ ] Kontrollcenter: ROCKNIX-eigene Helligkeits-/Lautstärke-Anzeige unterdrücken, wenn im CC geregelt wird
- [x] PortMaster: Ports nicht steuerbar – Ursache: seat1 `fallback yes` schnappt sich gptokeyb-Tastatur (19.10.2026 gelöst)
- [ ] Installer (mit CC, Etappe 4) – Geräteeinstellungen vom 19.10.2026 übernehmen:
      `seat seat0 attach "4660:22136:Fake_Keyboard"` in sway/config ·
      `set_setting rocknix.bottomscreen.type none` (lowerdeck aus) ·
      mako: `[summary~="^(Brightness|Volume):"] invisible=1` ·
      Deploy-Pfad CC: `/storage/.config/retrodualstation/controlcenter/`
- [ ] Idee (19.10.2026): Benutzerwechsel im Gameswitcher – je Benutzer eigene Savegames und
      Speicherstände (z. B. eigene Ordner pro Profil, beim Wechsel umschalten; RetroArch
      `savefile_directory`/`savestate_directory`, DraStic/DSperate prüfen)
- [ ] Einstellungsmenü wie am Smartphone (beschlossen 19.10.2026) – Aufruf über **Zahnrad-Symbol
      in der CC-Kopfzeile**; oben Kategorie-Kacheln, darunter Listen:
      - **Anzeige:** Theme, Theme je Modus (Dual/Single), Bildschirmschoner
      - **Spiele & Emulatoren:** Standard-Emulator/Core je System, Emulator-Einstellungen,
        Systeme ein-/ausblenden
      - **Controller:** Tastenbelegung, „Als Spieler 1 verwenden“
      - **Netzwerk:** WLAN, Bluetooth, SSH/Samba ein/aus
      - **System:** Updates, Systeminfo, Speicherplatz, Sprache, Zeitzone/Uhrzeit,
        Energie (automatischer Ruhemodus)
      - **RetroDualStation:** Dual/Single umschalten, CC-Einstellungen (Tastatur QWERTZ/QWERTY,
        Akzentfarbe, automatisch abdunkeln, Haltezeit, Kürzel erlauben)
      - später: RetroAchievements-Anmeldung, Benutzerwechsel (Tastatur QWERTZ/QWERTY, Haltezeit, Kürzel erlauben …)
- [ ] DraStic testen: Auto-Speichern/Laden, Tastaturtasten als Kürzel
- [ ] DraStic: großes Pausemenü vom RG DS übernehmen (`librgdsmenu.so`)
- [ ] DraStic: eigene Einstellungsoberfläche (`drastic.cfg`)

### Themes & Geräte
- [ ] dii-ess-aye: eigene Ansichten wie bei canvas-ds
- [ ] Version für das normale RG DS (640×480)
- [ ] optional: ES-Patch für die Option „Standard-Rastergröße“

### Eigener Auftritt (Idee 19.10.2026)
- [ ] Ladebildschirm „RetroDualStation“ auf beiden Bildschirmen zwischen ROCKNIX-Bootlogo und ES
      (eigener Dienst mit Overlay-Technik des Kontrollcenters, endet sobald ES da ist)
- [ ] Ladebildschirm im eigenen ES-Build (bisher `--no-splash`)
- [ ] Theme: RDS-Logo statt ROCKNIX-Logo in der Hauptansicht (nach Logo-Fertigstellung)
- [ ] optional: Startton
- Nicht machbar als Add-on: das allererste Bootlogo (fest in `rocknix-splash` im Startabbild) –
  nur mit eigenem ROCKNIX-Abbild, bewusst nicht geplant
- „Built on ROCKNIX“ bleibt in README/Danksagung; ROCKNIX-Logo nicht für uns verwenden

### Logo
- [ ] RDS-Monogramm auswählen und verfeinern (Entwürfe: Verbunden, Zwei Ebenen, Verwoben)
  – RDS = **R**etro**D**ual**S**tation; Farben Rot · Weiß · Blau (Easter Egg siehe Umbenennung; zufällig auch die Landesfarben Schleswig-Holsteins)
  – Favorit: Variante 3 „Verwoben“ mit Dual-Screen-Handheld
- [ ] danach: App-Symbol für DualStation Sync und Kontrollcenter ableiten

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
- [ ] Umbenennung in **DualStation Sync** (Favorit, greift den Leitsatz auf; Alternative: DualStation Dock), Hinweis „funktioniert auch mit ROCKNIXDS“; Repo-Umbenennung ist harmlos (GitHub leitet weiter), Texte/Fenstertitel/Starter anpassen
- [ ] Aufräumen: Branch `geraeteprofile` (v4.11.0) wird nicht genutzt

## Erledigt (Auszug)
- [x] v9: canvas-ds-Ansichten (Gamecarousel, Detailliert, Raster, Showcase, Spotlight), Links/Rechts im Dual-Modus, README mit Screenshots
- [x] Artwork Manager v5: Profil DualStation (`-hero` / `-icon` / `-box`), auf dem Gerät getestet
- [x] Kontrollcenter und Gameswitcher: Entwurf freigegeben
