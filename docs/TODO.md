# To-do – RetroDualStation & Artwork Manager

Stand: 25.10.2026 (nach v15.3) · Eine Liste für alles, damit nichts verloren geht. Erledigtes steht in den
Release-Notes (`docs/releases/`) und im Git-Verlauf.

> **Leitsatz:** RetroDualStation – one system, two screens, everything in sync.
>
> Vision: ein Ökosystem aus Emulation, Gaming, Artwork-Manager, Scraping und
> Achievements, das am Gerät und am PC ineinandergreift.

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

## Als Nächstes
- [ ] **Beobachten: advanced_drastic** (https://github.com/trngaje/advanced_drastic, vorerst nur im Blick behalten – Stand 24.10.2026: 370f053) – Update 23./24.10.2026: **RG DS mit
      zwei eigenen Fenstern** (vorher ein schwebendes Fenster + Sway-Zeilen; Skript kannte auch „RG DS Plus“).
      LD_PRELOAD-Hook für DraStic v2522, eigenes Menü (Auto-Speichern/Laden mit Slot, FPS, Save/Load-Taste, Cheats,
      falsches Mikrofon). Installer ersetzt den DraStic-Starter (eigenes drastic_v2522, eigenes LD_PRELOAD statt
      libdrastouch.so, beendet gptokeyb), Sicherung drastic.tar.gz + Deinstallation. **Keine Lizenz** → nicht mitliefern.
      Konflikte mit RDS: `fullscreen enable global` (Gameswitcher/Schnellwechsel/Sicherheitsnetz) und `touch_map`
      gehen von EINEM Fenster aus; F9–F12-Belegung. Plan: erst im Single-Modus auf dem RG DS testen (Fenster, Touch,
      Leistung); passt es, RDS erkennen lassen, ob advanced_drastic aktiv ist, und dann Fenster-/Touch-Eingriffe weglassen.
- [ ] **Automatischer Updater/Downloader** (Wunsch 25.10.2026) – bei bestehender Internetverbindung neue RDS-Version
      selbst finden und laden, statt die ZIP am PC zu holen und per SD/scp in ports zu kopieren. Ideen: Abfrage
      `api.github.com/repos/Ninte86hl/RetroDualStation/releases/latest` (Tag mit `rds-install/VERSION` vergleichen);
      Hinweis im CC („Update verfügbar: v…“) und Eintrag/Kachel „Update laden“; ZIP nach `/storage/roms/ports`
      laden (Fortschritt, genug Speicher prüfen, SHA256/Größe gegen die Release-Angaben), entpacken, dann wie
      bisher **Update RDS** (gleiche Sicherheitsnetze). Nur auf Wunsch laden, nie automatisch installieren; kein Netz →
      still nichts tun. Später: Release-Notes kurz im CC anzeigen. (Entscheidung 21.10.: Updates erst bei größerer
      Nutzerbasis – damit jetzt eingeplant.)
      Voraussetzung: RDS ist schon installiert – die Erstinstallation bleibt wie bisher (ZIP in ports). Ziel: Updates
      ohne PC, direkt am Gerät; möglichst einfach halten (eine Kachel, eine Rückfrage).
      Paket: eigenes Asset je Release **`rds-<version>-updater.zip`** (z. B. `rds-v15.4-updater.zip`), von
      `make-installer.py` mitgebaut. Nur was ein Update braucht (ohne canvas-ds, wenn unverändert → deutlich kleiner).
      Immer das neueste: `releases/latest` (kein Entwurf/keine Vorabversion), Asset per Namensmuster wählen, Version
      im Namen mit dem Tag vergleichen, Größe/Prüfsumme prüfen; ältere Versionen nie „aktualisieren“.
- [ ] **Idee, noch nicht entschieden (25.10.2026): Start aus ES ohne Auto-Laden, Fortsetzen nur über den Gameswitcher** – automatischer Stand
      wird weiter über Home kurz, Gameswitcher und CC-Beenden angelegt. Umsetzung: Installer setzt ES-Autoload aus
      (gesichert, Deinstallation stellt zurück); Gameswitcher lädt den Auto-Stand immer selbst (neu: DSperate, wie die
      Kachel „Automatisch“); Sonderwege fürs ES-Autoload (DSperate autosave=0 beim Neustart, RA-Reset verdecken) nur
      noch, wenn jemand ES-Autoload selbst einschaltet; Tour/Wiki: „Start aus ES = von vorn, Fortsetzen = Home 2×“.
      Offen: alle Systeme oder nur RetroArch/DraStic/DSperate? Zusätzlicher Schalter im CC?
- [ ] **ES `global.savestates`**: RDS setzt seit v13 „auto“ (Savestate-Manager aus) – ES gibt damit beim Start den
      nächsten freien Slot an RetroArch. Prüfen, ob ein anderer Wert den Manager ausblendet, ohne den Slot vorzugeben
      (für manuelles Speichern egal, das macht seit v15.3.1 das CC).
- [ ] **Präfix rds- für den Config-Ordner** – `/storage/.config/retrodualstation` → `/storage/.config/rds-config`
      beim nächsten ES-Build (Patch 004 liest `screens.cfg` dort, Pfad ist ins ES einkompiliert). Dann CC, Artwork
      Manager (`BASE`), Dienste, Installer (Umzug + Merker), Deinstallation und Doku mit umstellen.
- [ ] **Vergleich GPU-Treiber libmali vs. panfrost** (Wunsch 25.10.2026) – Eindruck: mit panfrost bessere Leistung in
      DS-Spielen (DraStic, DSperate). Auf beiden Geräten je Treiber messen: Gameswitcher-Kette (Mitschnitt wie
      25.10.: `journalctl -u rds-controlcenter -f -o short-precise`, gleiche Wechsel RA ↔ DraStic ↔ DSperate),
      FPS im Spiel (DraStic/DSperate-Anzeige, gleiche Stelle), Start-/Ladezeiten, dazu Touch, Bildschirmzuordnung und
      Overlays prüfen. Umschalten über die ROCKNIX-Einstellung (autostart `003-gpudriver`; genauen Schlüssel/Menüpunkt
      am Gerät nachsehen). Ergebnis als Tabelle; ggf. Empfehlung in der Doku, kein automatisches Umschalten durch RDS.
- [ ] **Navigationspfeile** (25.10.2026) – geplante Änderung, Details vergessen; beim nächsten Mal klären,
      wo genau (CC, Gameswitcher, ES?). Beeinträchtigt das laufende System nicht.
- [ ] **Installer: DraStic `compress_savestates = 0`** – eingebaut (25.10.2026); noch prüfen, ob alte komprimierte
      Savestates danach weiter laden.
- [ ] ES-Patch: In Listen fehlt auf Deutsch das ▲▼-Symbol in der Hinweisleiste. ROCKNIX übersetzt den Symbolnamen mit (`HelpPrompt(_("up/down"), …)` in `ComponentList.cpp` und `ComponentTab.cpp` → „Unknown help icon "hinauf/hinunter"“ im Log). Symbolnamen nicht übersetzen. (vorgemerkt 23.10.2026)
- [ ] Issue #5 (maniman303) beantworten: ScreenScraper im Dual-Build (v15), Bildschirm-Bereiche (Patch 004/005)
- [ ] Artwork Manager: Baustellen sammeln (Stichpunkte vom Nutzer) und der Reihe nach beheben – **Grundlage vor allen Erweiterungen**

## RetroDualStation

### Kontrollcenter & Co. (Details: [KONTROLLCENTER.md](KONTROLLCENTER.md))
- [ ] Zuklappen/Aufklappen berücksichtigen (Pause bleibt bis zum Aufklappen;
      „Unterer Screen aus“ nach dem Aufklappen beibehalten bzw. bewusst wieder einschalten)
- [ ] „Läuft gerade“ über die ES-Schnittstelle `http://localhost:1234/runningGame`
- [ ] Log-Manager für einfache Fehlersuche – Logs von Kontrollcenter, ES,
      RetroArch, DraStic, System an einer Stelle ansehen; „Fehlerbericht erstellen“ packt sie
      in eine Datei (z. B. `/storage/logs/`), die man per Netzwerkfreigabe holen kann
- [ ] Bluetooth-Controller wird **automatisch Spieler 1**, sobald er verbunden ist – ohne eigene Option
      (Entscheidung 22.10.2026; geringer Nutzen, da die RG-DS-Reihe keinen TV-Ausgang hat, aber bequem)
      (ES übergibt die Zuordnung per `--controllers` an runemu → setsettings →
      `input_playerN_joypad_index`, wirkt nur bei RetroArch; DraStic/DSperate prüfen)
- [ ] Koppeln während eines Spiels – runemu beendet `rocknix-bluetooth-agent`
      beim Spielstart; CC muss den Helfer bei Bedarf selbst starten (`systemd-run rocknix-bluetooth-agent`)
- [ ] DraStic testen: Auto-Speichern/Laden, Tastaturtasten als Kürzel
- [ ] Idee (23.10.2026): **Play Activity** – Spielzeit wie bei Switch/3DS. Daten liefert ES schon
      (`gamelist.xml`: `lastplayed`, `playcount`, `gametime`) – nichts neu protokollieren.
      Zuerst pro Spiel auf der Seite „Spiel“ im CC („14 Std · zuletzt gestern“), später Übersicht der
      meistgespielten Spiele im Einstellungsmenü. Vorher prüfen: zählt ES die Zeit auch bei Wechseln
      über den Gameswitcher (Ketten-Start, Patch 002) richtig? Akku-Restzeit/-Gesundheit bewusst nicht.
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
      - **Controller:** nur **Tastenbelegung** (Entscheidung 22.10.2026) – alle Anzeigen folgen der
        Einstellung dynamisch: Hinweiszeilen, Tastenseite und Tour im CC, Gameswitcher, Power-Menü,
        Artwork Manager und Meldungen zeigen immer die tatsächlich belegten Tasten
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
        CC/Menüs folgen dann dem jeweils freien Bildschirm

### Themes
- [ ] dii-ess-aye: eigene Ansichten wie bei canvas-ds
- [ ] optional: ES-Patch für die Option „Standard-Rastergröße“

### Eigener Auftritt
- [ ] Ladebildschirm „RetroDualStation“ auf beiden Bildschirmen zwischen ROCKNIX-Bootlogo und ES
      (eigener Dienst mit Overlay-Technik des Kontrollcenters, endet sobald ES da ist)
- [ ] Theme: RDS-Logo statt ROCKNIX-Logo in der Hauptansicht
- [ ] optional: Startton
- Nicht machbar als Add-on: das allererste Bootlogo (fest in `rocknix-splash` im Startabbild) –
  nur mit eigenem ROCKNIX-Abbild, bewusst nicht geplant
- „Built on ROCKNIX“ bleibt in README/Danksagung; ROCKNIX-Logo nicht für uns verwenden

### Technik & Wartung (beschlossen 21.10.2026)
- [ ] **RAM sparen im Kontrollcenter/Gameswitcher** – Bildercache (`Pen._png`) beim Schließen leeren und auf ~20 Bilder begrenzen; Zeichenpuffer (`_mm`, oben/Meldungen) beim Verbergen freigeben. Vorher/nachher messen: `ps -o pid,rss,args | grep "[r]ds_cc"`
- [ ] **Module statt einer Datei** – `rds_cc.py` erst aufteilen, wenn ein großes Feature ansteht (z. B. Einstellungsmenü): wayland · eingabe · emulatoren · kontrollcenter · gameswitcher · achievements · ui. Neue Teile gleich als eigenes Modul.
- Verworfen: CC und Gameswitcher als getrennte Prozesse – mehr RAM, Tastenabstimmung fehleranfällig, kein Tempogewinn (Engpass ist der Emulatorstart)

## Artwork Manager

### Grundlage
- [ ] Baustellen beheben (siehe oben)
- [ ] SGDB-Wiederholung bei Zeitüberschreitung
- [ ] Titelsuche verbessern, pro System der passende Weg:

  | System | Weg |
  |---|---|
  | DS/DSi, GBA | Seriennummer (Code gleich, letzter Buchstabe = Region) |
  | SNES | Seriennummer, Name als Rückfall |
  | GB/GBC | Seriennummer wo vorhanden, sonst Name |
  | NES, Master System, Mega Drive, PS1 | bereinigter Name + Ähnlichkeitswertung + Aliase |
  | CPS1–3 | Arcade-Datenbank (Hauptversion) |

  Reihenfolge: Seriennummer/Hauptversion → Name mit Wertung → Alias-Datei → manuelle Auswahl.
  Mit ScreenScraper (Dual-Build seit v15): Erkennung per Prüfsumme und Namen pro Region – ersetzt das meiste davon.

### Ausbau
- [ ] Logos übertragen (`romname-logo.png` → `<marquee>`)
- [ ] Metadaten (Beschreibung, Genre, Spieler, Jahr, Entwickler): ScreenScraper bevorzugt, sonst TheGamesDB/IGDB
- [ ] optional: Speicherplatz sparen (PNG-Farbreduktion, alte Scraper-Bilder verkleinern)

### PC-Programm (RocknixDS Artwork Manager)
- [ ] Linux-Test, Windows-Passwort-Login
- [ ] Desktop-Starter: Update kam einmal nicht automatisch an – prüfen
- [ ] Umbenennung in **DualStation Sync** (Favorit; Alternative: DualStation Dock), Hinweis „funktioniert auch mit ROCKNIXDS“; Texte/Fenstertitel/Starter anpassen
- [ ] Aufräumen: Branch `geraeteprofile` (v4.11.0) wird nicht genutzt
