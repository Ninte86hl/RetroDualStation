# To-do – RetroDualStation & Artwork Manager

Stand: 25.10.2026 (nach v15.2) · Eine Liste für alles, damit nichts verloren geht. Erledigtes steht in den
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
- [ ] **Vergleich GPU-Treiber libmali vs. panfrost** (Wunsch 25.10.2026) – Eindruck: mit panfrost bessere Leistung in
      DS-Spielen (DraStic, DSperate). Auf beiden Geräten je Treiber messen: Gameswitcher-Kette (Mitschnitt wie
      25.10.: `journalctl -u rds-controlcenter -f -o short-precise`, gleiche Wechsel RA ↔ DraStic ↔ DSperate),
      FPS im Spiel (DraStic/DSperate-Anzeige, gleiche Stelle), Start-/Ladezeiten, dazu Touch, Bildschirmzuordnung und
      Overlays prüfen. Umschalten über die ROCKNIX-Einstellung (autostart `003-gpudriver`; genauen Schlüssel/Menüpunkt
      am Gerät nachsehen). Ergebnis als Tabelle; ggf. Empfehlung in der Doku, kein automatisches Umschalten durch RDS.
- [ ] **Tour: veralteten Hinweis anpassen** – „einmal im Single-Screen-Modus scrapen“ beim Artwork Manager
      (Rest aus dem erledigten Punkt „Single-Modus: Kontrollcenter ruhen lassen“).
- [ ] **Spiel neu starten in DraStic und DSperate** (Wunsch 25.10.2026, nächste Runde) – wie bei RetroArch direkt im
      laufenden Emulator, aus dem CC (Seite „Spiel“) und mit Y im Gameswitcher. Prüfen: Reset-Kürzel/Menüpunkt in
      DraStic und DSperate, ob er sich per virtueller Taste auslösen lässt; sonst Neustart des Emulators ohne
      Auto-Laden. Zusammen mit dem Punkt „DSperate Neu starten (Y)“ unten angehen.
- [ ] **Kette DraStic → RetroArch beschleunigen** (Messung 25.10.2026, RG DS Plus) – läuft ein DraStic-Spiel als
      Zusatzspiel und man wechselt zu einem *anderen* RetroArch-Spiel als dem geparkten, dauert es ≈ 11 s:
      DraStic beenden ≈ 3 s, geparkten RetroArch aufwecken + über ES beenden ≈ 2 s, neues RetroArch-Spiel ≈ 6 s
      (runemu → Prozess 3,5–4,6 s). Idee: geparkten RetroArch direkt beenden statt sichtbar aufzuwecken (≈ 0,5 s,
      kein Aufblitzen). DraStic nicht hart beenden (`.dsv`-Spielstand). Übrige Werte: RA → DraStic 3,7 s,
      DraStic → DraStic 4,0–4,5 s, RA → RA (ES-Kette) 6,1 s, Speichern RA 0,1 s / DraStic ≈ 0,45 s, Home kurz 0,4 s.
- [ ] **Navigationspfeile** (25.10.2026) – geplante Änderung, Details vergessen; beim nächsten Mal klären,
      wo genau (CC, Gameswitcher, ES?). Beeinträchtigt das laufende System nicht.
- [ ] **Savestates: Übergang für bestehende Nutzer** (25.10.2026) – Platz 0 ist jetzt der automatische Stand.
      Eigene Stände auf Platz 0 (v. a. DSperate, z. B. `AMCE.0.dss`) einmalig in den nächsten freien Slot verschieben;
      alte RetroArch-Gameswitcher-Stände auf Platz 9 (`.state9`) erscheinen sonst als Slot 9.
- [ ] **Installer: DraStic `compress_savestates = 0`** – eingebaut (25.10.2026); noch prüfen, ob alte komprimierte
      Savestates danach weiter laden.
- [ ] **DSperate „Neu starten“ (Y im Gameswitcher)** prüfen – Autoload kommt per `--autoload` aus ROCKNIX, nicht aus
      dsperate.ini; das Abschalten im CC greift vermutlich nicht.
- [ ] **Uninstaller: Sicherungen zurückspielen** (24.10.2026) – `system.cfg`-Werte, Sway und mako stellt er schon her,
      aber nicht: RetroArch-Kürzel (`retroarch.cfg.vor-rds-kuerzel`), DSperate (`dsperate.ini.vor-rds-kuerzel`, auch `toasts`),
      DraStic (`drastic.cfg.vor-rds-kuerzel`), ES-Tastenbelegung (`es_input.cfg.before-rds`), RetroArch „Rückfragen und
      Einblendungen aus“ und PS1-Core (nur im Log, keine Sicherung). Wie bei Multi Pop: nur zurückspielen, wenn die Datei
      seit der Installation unverändert ist (Prüfsumme beim Installieren merken) – sonst nicht überschreiben und im Log/Hinweis
      nennen, damit spätere eigene Änderungen erhalten bleiben. Kein ES-Build nötig.
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
