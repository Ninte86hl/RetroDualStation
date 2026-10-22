# To-do – RetroDualStation & Artwork Manager

Stand: 20.10.2026 · Eine Liste für alles, damit nichts verloren geht.

> **Leitsatz:** RetroDualStation – one system, two screens, everything in sync.
>
> Vision: ein Ökosystem aus Emulation, Gaming, Artwork-Manager, Scraping und
> Achievements, das am Gerät und am PC ineinandergreift. Der Leitsatz kommt auf
> die GitHub-Seite, sobald Kontrollcenter und Desktop-Begleiter da sind.

Neue Ideen kommen erst hier rein, dann wird entschieden, wann sie dran sind.

> **Grundsatz:** Einfach und gut steuerbar. Niemand muss Technik verstehen, um RetroDualStation
> zu nutzen – Bedienung wie vom Smartphone gewohnt, schnell, mit Touch und Tasten. Sicherheit
> vor Funktionsumfang: stabile ROCKNIX-Basis, jederzeit mit einem Tipp zurück.

## Grundsatz Community (21.10.2026)
- Hinweise und Tipps aus der Community, die die Entwicklung weiterbringen, werden **immer** in CREDITS.md (Abschnitt „Community“) mit Name und Link zum Issue genannt – Transparenz und Rückmeldung an die Community.

## Bedienregeln (gelten für alle Oberflächen)

- **Hinweiszeilen:** Taste/Bedienelement **fett**, danach „– Erklärung“, mehrere Einträge mit „·“ getrennt.
  Beispiel: **▲ ▼** – System wählen · **Start** – Einzelsuche · **Select** – Mehrfachsuche.
- Umgesetzt im Artwork Manager, Kontrollcenter (Fußzeilen, WLAN/Bluetooth, Bildschirmtastatur, Power-Menü) und Gameswitcher (`Pen.hint`).

## Erledigt 20.10.2026 – Release v12 veröffentlicht (20.10.2026)
- [x] **Artwork Manager am Gerät** (Ports): zwei Bildschirme (oben Mix-Vorschau, unten Listen), Tabs Boxart/Cartridge/Image,
      Einzel- und Mehrfachsuche, globale Spielesuche, Filter, Icon-Editor mit iiSU-Rahmen, eigene Bilder (`eigene/`),
      Einstellungen (API-Key, Sicherung, M3U, Wiederherstellen, Cache, Log), Englisch, Pillow im Installer
- [x] Mehrteilige Spiele → `.m3u` (Discs ausgeblendet, Sicherung `gamelist.xml.vor-m3u`)
- [x] Arcade (FBNeo-Namen), PS1 und CPS1–3 im Artwork Manager
- [x] PS1: Installer setzt `pcsx_rearmed`, wenn der gewählte Core fehlt
- [x] **Tour** am Gerät (einmalig, erneut mit Select im CC) + `docs/TOUR.md`/`TOUR.de.md` mit Screenshots
- [x] Hinweiszeilen mit fetten Tasten überall (`Pen.hint`)
- [x] README EN/DE: Artwork Manager statt „DualStation Sync“
- [x] Home 2× im Spiel: direkt zum vorherigen Spiel (wie OnionOS)
- [x] ES-Patch 003: Bluetooth auf einem Screen, system.cfg neu laden, B ohne Navigationsleiste, Y-Spielesuche

### Offen nach v12
- [x] Issue #5 (maniman303): Artwork-Standard dokumentiert (`docs/ARTWORK.md`, 20.10.2026)
- [ ] Issue #5: ScreenScraper-Dev-Kennung beantragt (20.10.2026, Forum „ScreenScraper WebAPI“) – danach ES-Build über GitHub Actions mit Secret
- [x] Issue #5: Bildschirm-Bereiche im ES-Patch (Patch 004/005, getestet 20.10.2026); Konzept: [BILDSCHIRME.md](BILDSCHIRME.md)
- [~] Artwork Manager: libretro-Thumbnails als Quelle ohne Schlüssel – verworfen (22.10.2026): ScreenScraper im Dual-Build (v15) findet die Bilder und legt eine korrekte gamelist.xml an
- [ ] Issue #5 beantworten, sobald Punkte stehen
- [ ] Artwork Manager: SGDB-Wiederholung bei Zeitüberschreitung, M3U in Unterordnern
- [ ] PC-Programm: Linux-Test, Windows-Passwort-Login
- [ ] Umbenennungs-Reste (siehe unten)

## Priorität (festgelegt 20.10.2026)
Keine neuen Funktionen, bis diese fertig sind – neue Ideen nur notieren.
1. ✅ **Etappe 5: Gameswitcher** (fertig 20.10.2026: RetroArch, DraStic, DSperate, Ports; ES-Ketten-Start, Ladebildschirm; Release v11 offen) (Return/Home-Taste, Auto-Speichern/Laden) 
   - Liste der zuletzt gespielten Spiele mit **Screenshot vom letzten Zeitpunkt** (beim Auto-Speichern)
   - Tasten: **A** letzten Savestate laden (weiterspielen) · **Y** Spiel neu starten ohne Savestate
     (normaler Spielstand im Spiel/SRAM bleibt unberührt) ·
     **X** aus der Liste entfernen (Speicherstand bleibt) · **B** schließen
2. ✅ **Etappe 2: Seite „Spiel“** im CC (fertig 20.10.2026; offen: Steuerung, DSperate)
3. **Version für das normale RG DS** (640×480) – sobald 1 und 2 gebaut und getestet sind

Danach abwägen, was als Nächstes ausgebaut wird.

## Als Nächstes
- [x] Bestandsaufnahme auf dem RG DS Plus (Ergebnis in [KONTROLLCENTER.md](KONTROLLCENTER.md))
- [x] Entscheidung (19.10.2026): Kontrollcenter als **Eigenentwicklung** (eigener Code, MIT wie der Rest; lowerdeck nur als Hinweis, dass der Weg funktioniert – kein Code übernommen)
- [ ] Artwork Manager: Baustellen sammeln (Stichpunkte vom Nutzer) und der Reihe nach beheben – **Grundlage vor allen Erweiterungen**

## RetroDualStation

### Umbenennung ROCKNIX DualStation → RetroDualStation (beschlossen 19.10.2026)
- [x] GitHub-Repository umbenennen → `Ninte86hl/RetroDualStation` (21.10.2026, Links im Repo angepasst)
- [ ] README (EN/DE), CREDITS, Overlay-README, Doku: Name und Leitsatz
- [ ] Installer/Uninstaller, Ports-Einträge, Meldungen, Log-Namen; ZIP-Namen **mit v14** (Übergang für alte Installationen)
- [ ] Ankündigung mit neuem Namen und Logo
- Easter Egg (bewusst nicht erklärt): RDS liest sich auch als **R**OCKNIX **D**ual**S**tation,
  Farben Rot (ROCKNIX) · Blau (JELOS) · Weiß – für Kenner der Szene ableitbar,
  die Basis wird in den Danksagungen genannt

### Kontrollcenter & Co. (Details: [KONTROLLCENTER.md](KONTROLLCENTER.md))
- [x] Etappe 1 (abgeschlossen 19.10.2026): Schnelleinstellungen, Seiten, Anbernic-Taste, Pause, Hell/Dunkel, Akzentfarbe, WLAN/Bluetooth-Untermenüs, Tastatur, externe Controller, Englisch, Autostart
- [x] Etappe 2: Seite „Spiel“ – Infoansicht, Speichern/Laden mit Slot-Auswahl und Vorschau, Löschen (X X / Mülleimer), Emulator-Menü, Neu starten, Vorspulen, Zeitlupe, Screenshot, Beenden (getestet 20.10.2026)
- [x] Seite „Spiel“: Tastenbelegung je System/Emulator, DSperate Speichern/Laden/Slots/Menü, einheitliche Kürzel (21.10.2026)
- [x] DraStic: Slots 0–8 mit Vorschaubild und Emulator-Menü über das CC (getestet 21.10.2026); Kürzel-Kombinationen kennt DraStic nicht; Vorspulen über das CC (R3 fehlt am Gerät) getestet
- [x] DraStic: Menü (R3) und Vorspulen (Geister-Stick) nur über das CC, L3 frei – getestet 21.10.2026
- [~] DraStic-Menü vergrößern: `librgdsmenu.so` auf dem RG DS Plus nicht vorhanden – zurückgestellt (21.10.2026)
- [~] RetroArch-Kürzel im CC anpassen – verworfen (21.10.2026): einheitliches festes Schema reicht
- [x] Etappe 4: RetroArch-Touchmenü (lowerdeck) ersetzt, CC im Installer (19.10.2026, Test der ZIP ausstehend)
- [x] Etappe 5: Gameswitcher (Return/Home-Taste, Auto-Speichern/Laden) – 20.10.2026
- [x] ES (eigener Dual-Build): Bluetooth-Menü (Gerät koppeln) auf einen Bildschirm begrenzt – Patch 003 (20.10.2026)
- [x] ES (eigener Dual-Build): `system.cfg` wird beim Öffnen des Hauptmenüs neu eingelesen, wenn sie sich geändert hat – Patch 003 (20.10.2026)
- [x] ES: **B** in der Systemliste ohne Navigationsleiste („Go to manufacturer“), **Y** = Spielesuche über alle Systeme (Trefferliste, A springt zum Spiel) – Patch 003 (20.10.2026)
- [x] Kontrollcenter: Pause in RetroArch, DraStic und DSperate getestet (19.10.2026)
- [x] Kontrollcenter: Mini-Power-Menü wie bei Android – Ausschalten, Neustart, Ruhemodus,
      ES neu starten (mit Rückfrage; laufendes Spiel vorher speichern/beenden).
      Aufruf (entschieden 19.10.2026): **Ein/Aus-Taste kurz drücken**; Ruhemodus per Zuklappen
      (Hall-Sensor, bleibt bei ROCKNIX) oder über den ersten Knopf im Menü
- [ ] Kontrollcenter: Zuklappen/Aufklappen berücksichtigen (Pause bleibt bis zum Aufklappen;
      „Unterer Screen aus“ nach dem Aufklappen beibehalten bzw. bewusst wieder einschalten)
- [ ] Kontrollcenter: „Läuft gerade“ über die ES-Schnittstelle `http://localhost:1234/runningGame`
- [~] FPS-Symbol auf der Seite „Spiel“ – verworfen (21.10.2026): CC kann FPS nicht messen; RetroArch bräuchte die abgeschaltete Bildschirmschrift (Meldungen), DraStic hat keine Anzeige. DSperate: Anbernic + Y.
- [x] Vibration (21.10.2026): kurzes Feedback in Gameswitcher, CC und Power-Menü, Schalter oben im CC
- [ ] Kontrollcenter: Log-Manager für einfache Fehlersuche – Logs von Kontrollcenter, ES,
      RetroArch, DraStic, System an einer Stelle ansehen; „Fehlerbericht erstellen“ packt sie
      in eine Datei (z. B. `/storage/logs/`), die man per Netzwerkfreigabe holen kann
- [ ] Kontrollcenter: „Als Spieler 1 verwenden“ für Controller im Bluetooth-Untermenü
      (ES übergibt die Zuordnung per `--controllers` an runemu → setsettings →
      `input_playerN_joypad_index`, wirkt nur bei RetroArch; DraStic/DSperate prüfen)
- [ ] Kontrollcenter: Koppeln während eines Spiels – runemu beendet `rocknix-bluetooth-agent`
      beim Spielstart; CC muss den Helfer bei Bedarf selbst starten (`systemd-run rocknix-bluetooth-agent`)
- [x] Etappe 3: RetroAchievements – Seite 3, Erfolg öffnen, Freischalt-Meldung, Lautstärke-Anzeige (21.10.2026)
      - **Benachrichtigung:** kurzes Overlay auf dem unteren Bildschirm, wenn ein Erfolg
        freigeschaltet wird (Symbol, Titel, Punkte; blendet sich selbst aus, Spiel läuft weiter)
      - **Erfolge-Übersicht** (CC-Seite „RetroAchievements“): erledigte und offene Erfolge
        des laufenden Spiels mit Symbol, Beschreibung, Punkten und Fortschritt
- [x] Kontrollcenter: RetroArch-Touchflächen (Savestates etc.) auf dem unteren Screen bei „Screen aus“ prüfen – evtl. abschalten
- [x] Kontrollcenter: ROCKNIX-eigene Helligkeits-/Lautstärke-Anzeige unterdrücken, wenn im CC geregelt wird
- [x] PortMaster: Ports nicht steuerbar – Ursache: seat1 `fallback yes` schnappt sich gptokeyb-Tastatur (19.10.2026 gelöst)
- [x] Installer (mit CC, Etappe 4) – Geräteeinstellungen vom 19.10.2026 übernehmen:
      `seat seat0 attach "4660:22136:Fake_Keyboard"` in sway/config ·
      `set_setting rocknix.bottomscreen.type none` (lowerdeck aus) ·
      mako: `[summary~="^(Brightness|Volume):"] invisible=1` ·
      Deploy-Pfad CC: `/storage/.config/retrodualstation/controlcenter/`
- [~] Idee (19.10.2026): Benutzerwechsel im Gameswitcher – verworfen (22.10.2026): eigene Ordner pro Profil
      wären nach dem Deinstallieren von RDS nicht mehr sinnvoll nutzbar (RDS soll restlos entfernbar bleiben)
- [ ] Idee (20.10.2026, ohne Priorität): **Einrichtungsassistent** beim ersten Start nach der
      Installation – WLAN, Zeitzone, Sprache, Theme, kurze Einführung in Anbernic-/Power-Taste;
      überspringbar, später aus den Einstellungen erneut aufrufbar (Anregung: BananaLinux)
- [ ] Idee (20.10.2026, ohne Priorität): **Sicherheit** – prüfen, ob ROCKNIX im Ruhemodus bei
      leerem Akku sauber herunterfährt; sonst ergänzen (Anregung: BananaLinux)
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
        + **CC anpassen** wie Schnelleinstellungen am Handy: welche Kacheln/Regler sichtbar,
        Reihenfolge; auf der Seite „Spiel“ wählen, welche Kürzel/Funktionen (Savestate laden/
        speichern, Screenshot, Vorspulen …) angezeigt werden
      - Darstellung folgt Hell/Dunkel und Akzentfarbe des CC (Mockup: docs/kontrollcenter/einstellungen-mockup.png; Dual-Screen-Entwurf 21.10.2026 (lokal) – **so freigegeben zur Umsetzung**; Kategorie-Farben: Anzeige blau, Spiele grün, Controller violett, Netzwerk orange, System gelb, RDS rot/weiß)
      - später: RetroAchievements-Anmeldung
      - Nur unterer Bildschirm (wie CC); oben optional später Erklärung zur gewählten Einstellung
      - ES-Patch: **Start kurz** → Einstellungsmenü im CC (Nachricht an CC),
        **Start lang** → originales ES-Menü als Rückfall
  - Gestaltung (21.10.2026): unten Kategorien als wischbares Karussell wie canvas-ds, darunter die Einstellungen
    der Kategorie; oben Erklärung in Klartext mit 1:1-Bild. Schreibt in dieselbe `system.cfg` wie ES.
  - Bewusst **nicht** enthalten (Entscheidung 21.10.2026): Updates (erst bei größerer Nutzerbasis), Formatieren
    (im Single-Modus möglich; RDS ist restlos deinstallierbar), Overclocking (erst in ROCKNIX selbst ausprobieren) –
    als Einzelentwickler zu großes Unterfangen und Risiko.
- [ ] Vision (20.10.2026): ES nur noch als Anzeige/Theme-Engine, Bedienung über eigene Overlays
      auf dem unteren Bildschirm:
      - Bestandsaufnahme: welche ES-Dialoge öffnen sich per Taste in Systemliste und Spieleliste
        (Start, Select, X, Y, L/R …) – je Dialog entscheiden: ersetzen, behalten, weglassen
      - ROCKNIX-Schnellstartmenü wird überflüssig (CC deckt es ab)
      - Overlay **Spielesuche** (Bildschirmtastatur, Ergebnisse mit Icons, Sprung in ES-Liste)
      - Overlay **Spiel-Einstellungen** (per game: Emulator/Core, Seitenverhältnis, Shader …)
      - Idee: **Bildschirmwahl** je System/Spiel (auf welchem Screen gespielt wird);
        CC/Menüs folgen dann dem jeweils freien Bildschirm (Tastatur QWERTZ/QWERTY, Haltezeit, Kürzel erlauben …)
- [ ] DraStic testen: Auto-Speichern/Laden, Tastaturtasten als Kürzel
- ~~DraStic: großes Pausemenü / eigene DraStic-UI~~ – verworfen 20.10.2026 (Reverse Engineering, Lizenz, Aufwand)

### Normales RG DS (Plan 21.10.2026)
- Gleiches ROCKNIX-Image (RK3566-Build, SoC rk3568) → **kein zweiter ES-Build**, Patches 001–008 gelten für beide
- Erkennung über den Device Tree: RG DS Plus = Modell `Anbernic RG DS Plus`, compatible `anbernic,rg-ds-plus` (Ausgabe DSI-2 u. a., 1024 × 768); normales RG DS: Werte von einem Tester holen
- [ ] Geräteprofil: Auflösung, Ausgabenamen, Tastencodes, Helligkeitspfade, Vibration ja/nein
- [ ] Installer: beide Modelle zulassen, `screens.cfg` und Tastenschema je Profil
- [ ] Kontrollcenter/Gameswitcher: feste 1024 × 768 und Ausgabenamen durch das Profil ersetzen, Layout auf 640 × 480 skalieren (Hauptarbeit; dabei in Module aufteilen)
- [ ] canvas-ds und Artwork Manager auf 640 × 480 prüfen
- [x] Test auf echtem RG DS (21.10.2026, eigenes Gerät)
- Entscheidung 21.10.2026: ES-Menüschrift auf dem RG DS bleibt größer als maßstabsgetreu (ES-Regel für Bildschirme ≤ 480 px) – bewusste Usability-Entscheidung, Menüs scrollen dafür

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

### Nächste Version (Wunsch 21.10.2026)
- [ ] ES-Quick-Access/Beenden-Menü: **FAST SHUTDOWN SYSTEM** im Dual-Modus ausblenden (doppelte Option neben *Shutdown system*). Kleiner ES-Patch 010: Eintrag in `GuiMenu.cpp` (Beenden-Menü) nur ohne `RdsScreens::active()` anlegen.

### Technik & Wartung (beschlossen 21.10.2026)
- [ ] **v14: RAM sparen im Kontrollcenter/Gameswitcher** – Bildercache (`Pen._png`) beim Schließen leeren und auf ~20 Bilder begrenzen; Zeichenpuffer (`_mm`, oben/Meldungen) beim Verbergen freigeben. Vorher/nachher messen: `ps -o pid,rss,args | grep "[r]ds_cc"`
- [ ] **Module statt einer Datei** – `rds_cc.py` (~5.500 Zeilen) erst aufteilen, wenn ein großes Feature ansteht (Einstellungsmenü oder normales RG DS): z. B. wayland · eingabe · emulatoren · kontrollcenter · gameswitcher · achievements · ui. Neue Teile gleich als eigenes Modul.
- Verworfen: CC und Gameswitcher als getrennte Prozesse – mehr RAM, Tastenabstimmung fehleranfällig, kein Tempogewinn (Engpass ist der Emulatorstart)

### Scraper
- [x] ScreenScraper-Entwicklerzugang beantragt (20.10.2026, Antwort ausstehend)
- Alternative, falls ScreenScraper absagt: IGDB-/SteamGridDB-Scraper aus maniman303s ES-Fork (Branch `dual_screen_support`, nur Nutzer-Zugangsdaten; Issue #5)
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
