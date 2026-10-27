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
- [x] **„Bildschirme tauschen“ (Kachel „Tauschen“ + L3) – v15.3.2 veröffentlicht 25.10.** – DraStic: SWAP_SCREENS auf F8 (321,
      Installer-Merker drastic-kuerzel-v4), Touch nimmt DraStic selbst mit (ROCKNIX-Zuordnung DSI-2 lassen – DSI-1 macht es kaputt, mirror_touch unnötig, Plus 25.10. ok);
      „Follow 3D Renderer“ (ES-Option follow_3d_renderer → fix_main_2d_screen über start_drastic.sh) auch vor dem Start
      gesetzt und frisch aus ES gestartet (ohne Stand): Intro flackert, beide Bildschirme zeigen dasselbe Bild, Touch geht
      nicht (RG DS 25.10.) → in der ROCKNIX-DraStic mit zwei Bildschirmen unbrauchbar, L3 bleibt. Spielende getauscht →
      screen_swap = 0. DSperate: screen_swap tauscht im Zwei-Fenster-Betrieb nicht (auch von Hand) → nur DraStic. Zelda-Laden, Neustart
      getauscht (DraStic merkt sich den Tausch nicht) auf RG DS + Plus ok.
- [ ] **DraStic: Touchbild landet oben (Zelda Phantom Hourglass, Laden)** (gemeldet 25.10.2026) – Gegenstand wird oben
      angezeigt, lässt sich nicht antippen. Vermutung: Spiel tauscht intern die DS-Bildschirme, DraStic folgt
      („Follow 3D renderer“/automatischer Tausch) und legt das Touchbild auf den oberen echten Bildschirm ohne Touch.
      Tipp „vertikal statt horizontal“ gilt für Ein-Bildschirm-Geräte. Klären: Bildschirm-Optionen in drastic.cfg,
      Screenshot oben im Laden. Lösung: Tausch-Option aus (Installer, gesichert) und/oder SWAP_SCREENS als Kachel/Kürzel.
      Stand Plus: screen_orientation = 1 (ROCKNIX, nicht ändern), screen_swap = 0, **fix_main_2d_screen = 0** (Verdacht:
      DraStic folgt dem Hauptbild-Wechsel des Spiels), SWAP_SCREENS unbelegt. Test im Laden: DraStic-Menü „Swap screens“,
      sonst „Fix main 2D screen“ = an. Je nach Ergebnis: fix_main_2d_screen = 1 als Standard ODER SWAP_SCREENS auf
      virtuelle Taste + CC-Kachel „Bildschirme tauschen“.
      **Test 25.10.: bestätigt** – „Fix main 2D screen“ flackert (raus). „Swap screens“ + Touch auf DSI-1
      (`swaymsg input "1046:911:Goodix_Capacitive_TouchScreen" map_to_output DSI-1`) → Gegenstand antippbar. Die
      ROCKNIX-DraStic folgt dem Bildschirmwechsel des Spiels nicht; automatisch nicht erkennbar. **Plan:** CC-Kachel
      „Bildschirme tauschen“ (Seite Spiel) + Anbernic-Kürzel: SWAP_SCREENS auf freie virtuelle Taste (F8?) drücken UND
      Touch-Zuordnung DSI-2 ↔ DSI-1 umschalten; Zustand merken, beim Spielwechsel/-ende zurücksetzen (touch_map).
      Außerdem: Szene in DSperate testen; advanced_drastic passt Touch auf dem RG DS dynamisch an (siehe dort).
- [ ] **Versuch: DraStic vertikal statt horizontal** (Idee 25.10.) – Flackern/gleiches Bild mit „Follow 3D Renderer“
      evtl. Folge der horizontalen Anordnung (screen_orientation = 1, Fenster global über beide Ausgänge nebeneinander).
      Vertikal hieße: Sway-Ausgänge übereinander + screen_orientation vertikal – betrifft ES (screens.cfg), CC, Touch-
      Regel. Erst nur vorübergehend testen (Sway-Positionen per swaymsg, drastic.cfg gesichert); L3 bleibt bis dahin.
      **Test 25.10. (RG DS, tools/drastic-vertical-test.sh):** screen_orientation = 0 + Ausgänge übereinander → Menü und
      Spiel richtig, Tasten gehen, **Touch nie** (map_to_output DSI-1, *, map_to_region rechte/linke Hälfte). ROCKNIX lädt
      /usr/lib/libdrastouch.so (LD_PRELOAD, ersetzt SDL Touch→Maus) – rechnet offenbar fest waagerecht. → verworfen.
      Bekannt seit v8 (Wiki Gut zu wissen): Follow 3D Renderer = An → Touch geht nicht, „Auto“ nötig.
      **Neuer Anlauf 25.10. abends (tools/drastic-stacked):** RG DS hat ZWEI Touchscreens mit gleicher Kennung
      (event1 oben, event2 unten, je 640×480 roh). ROCKNIX legt per udev-Kalibrierung oben → linke, unten → rechte
      Hälfte der zugeordneten Ausgabe; libdrastouch (waagerecht) verdoppelt x. Neuere libdrastouch (ROCKNIX ab 6.10.,
      DSHOOK_WINDOW_SIZE) kann übereinander; eigener Build mit DSHOOK_RDS_SPLIT (linke Hälfte verwerfen, rechte strecken).
      Sway-calibration_matrix NICHT setzen – überschreibt die udev-Matrizen beider Panels (Neustart stellt sie wieder her).
      **Ergebnis 25.10. (Diagnose-ROM, RG DS):** Bildschirme übereinander + screen_orientation 0 →
      eigene libdrastouch (DSHOOK_WINDOW_SIZE + DSHOOK_RDS_SPLIT, map_to_output DSI-1): Touch unten genau, oben ignoriert,
      Menü richtig, auch nach DraStic-Menü. ROCKNIX-libdrastouch (1.10.) + map_to_region -320 480 640 480: Touch ebenso
      richtig, aber Menü nur linke Hälfte oben (rechnet waagerecht). Mit neuerer ROCKNIX-Bibliothek wäre es
      map_to_region -640 480 1280 480 + DSHOOK_WINDOW_SIZE – die Variable setzt ROCKNIX aber nur für den Duo Lite.
      Einhängen: ES führt /storage/.emulationstation/scripts/game-start|game-end/*.sh aus (Argumente: ROM, Name),
      aber OHNE zu warten (game-start +0,4 s, DraStic-Prozess +2,0 s). Offen: Weg ohne Bind-Mount für die eigene
      Bibliothek, Umgebungsvariable ohne Startskript (Bibliothek erkennt übereinander selbst?), Schnellwechsel/
      Gameswitcher-Kette, RG DS Plus (1024×768), ES während DraStic übereinander. Idee: Verbesserung an ROCKNIX
      vorschlagen (libdrastouch erkennt übereinander liegende Ausgänge und zwei Panels selbst).
- [x] **Durchbruch Zelda PH: Threaded 3D = Aus → DraStic tauscht die Bildschirme von selbst richtig** (RG DS 25.10.,
      Hinweis GammaOSNext#225: der Thread-Renderer vertauscht oben/unten, die Touch-Ebene bleibt). ES-Spieleinstellung
      `nds["<rom>"].threaded_3d=0`. Touch im Laden ok, Plus ok (25.10.). Offen: Leistung (Ruckeln?). Dann: Wiki „Gut zu wissen“, evtl.
      Liste bekannter Spiele (Spiel-Einstellung vorschlagen/setzen, gesichert), L3 bleibt als Notlösung.
- [x] **Verwaistes gptokeyb (Plus 26.10.)** – nach hartem Ende/Neustart von DraStic lief gptokeyb weiter → ES bekam jede
      Taste doppelt (Navigation springt, Doppelklick öffnet Menü). CC beendet jetzt 2 s nach Rückkehr in ES jedes
      gptokeyb, dessen „-sudokill“-Ziel nicht mehr läuft (v15.3.3).
- [ ] **Beschädigter automatischer Stand (Plus 26.10.)** – Zelda _0.dss ließ DraStic beim Start hängen (nach Laden des
      Spielstands, Ursache vermutlich unterbrochenes Speichern/Neustart). Idee: CC/Start erkennt Hänger (kein Fenster
      nach x s) bzw. prüft die Datei und startet ohne Stand; Stand beiseitelegen statt löschen.
- [x] **Mikrofon DraStic (26.10.)** – gelöst in v15.3.3 (eigenes Geräusch + medium) – ROCKNIX microphone.wav = 48 kHz weißes Rauschen (rms 14k); Zelda PH-Kerzen
      reagieren darauf nicht (L3 kommt an, Diagnose-ROM zeigt Pegel). advanced_drastic liefert 11 025 Hz, übersteuertes
      Rauschen (rms 27k) – Test läuft (Plus). Datei ohne Lizenz → bei Erfolg eigenes gleichwertiges Geräusch erzeugen.
      Echtes Mikrofon: high (0,03) löst durch Grundrauschen dauerhaft aus (Gain 27 dB) → medium/low testen.
- [x] **v15.3.3/v15.3.4: Mikrofon DraStic** (26.10.) – ERLEDIGT in v15.3.4 (veröffentlicht 26.10. abends): CC hört
      selbst ab (mic_watch, Schwelle 0,30), ROCKNIX-Erkennung aus. Plus: Pusten + L3 ✓, Reden löst nicht aus. RG DS: nur L3
      (Mikrofon liefert Rauschen, Gerätebaum – Fehlerbericht an ROCKNIX offen). Alter Stand: – Lösung: eigenes Pust-Geräusch (installer/payload/drastic/rds-microphone.wav,
      11 025 Hz übersteuert) + ROCKNIX-Erkennung nds.microphone_sensitivity (RDS-Standard 0.15, nur wenn aus/leer; Merker
      mikrofon.done) + L3 über das CC als Rollen-Taste (virtuelle Tastatur; Joypad-Belegung controls_b allein erkannte
      Zelda NICHT). Zelda-Kerzen (Plus): Pusten ✓ (high), L3 ✓. Offen: medium/low gegen Fehlauslösen, RG DS, Release.
      Testgeräte: controls_b[FAKE_MICROPHONE] von Hand auf 327 zurück.
- [ ] **Neu 25.10. 21:40: Follow 3D Renderer funktioniert auf dem RG DS** – Touch-Bild folgt der 3D-Einheit und liegt
      dann OBEN; der RG DS hat oben einen zweiten Touchscreen (event1), also oben tippen. Der RG DS Plus hat nur EINEN
      Touchscreen → dort „Touch geht nicht“ (deshalb nie aufgefallen; erklärt auch den v8-Tipp „Follow 3D auf Auto“).
      Flackern nur bei 3D auf beiden Bildschirmen (Titelbild: 3D-Einheit wechselt jedes Bild) – Spiel ruhig. Wiki,
      Release-Notes richtiggestellt. Offen: Leistung (Zelda hatte noch Threaded 3D aus – Follow 3D + Threaded an testen).
- [ ] **Neue ROCKNIX-Nightly (Plus, eigene SD-Karte, ab 26.10.)** – seit 20261001: rk3566 auf **InputPlumber** umgestellt
      (10.–19.10.), **Anbernic-„F“-Taste sendet KEY_F1** (21.10.), RG-DS-Dual-Screen-Fixes (Pad in ES nach Touch),
      ES-Update + Cursor-Ausblenden, höhere CPU-OPP, PanVK, CMA 32 MB, libdrastouch DSHOOK_WINDOW_SIZE, DSperate 3.0.5.
      Prüfen mit tools/rds-nightly-check.sh (vor und nach RDS-Installation): Gerätenamen (JOYPAD_NAME, inject_keys),
      Anbernic/Home-Erkennung im CC, Sway-Regeln, unser ES-Binary, Touch, Mikrofon.
- [ ] **Threaded 3D global aus?** (Frage 25.10.) – erst messen: RG DS + Plus, 2–3 anspruchsvolle Spiele (Mario Kart DS,
      Zelda auf See, Kampf), Bildzähler (DraStic-Menü → Show frame counter) mit/ohne. Kein Verlust → Installer stellt
      nds.threaded_3d=0 global (gesichert, Deinstallation rückgängig); sonst Tipp pro Spiel lassen.
- [ ] **drastic.cfg war leer (RG DS 25.10. 20:10)** – nach Vertikal-Test/Beenden 0 Bytes; aus dem Plus wiederhergestellt.
      Ursache unklar (DraStic beim Schreiben beendet? Test-Skript hatte keinen Schutz – nachgerüstet). Überlegen: CC/Installer
      prüft nach DraStic-Ende auf leere drastic.cfg und stellt eine gute Kopie wieder her.
- [ ] **Prüfen: DSperate v3.0.5** (github.com/beebono/DSperate, 21.10.2026) – neu: `--saves`/`--states`, Fehlerbild beim
      Start, Vulkan-Ausgabe zuerst bei `video.gpu_present = true` (Render-Pass), RGA ganzzahlig, Fix: PipeWire-Taktung
      (RLIMIT_RTTIME-Abbruch), GPU-Ausgabe bleibt nach Menü, JIT/2D-Ruckler, 3D-Kanten. Einbindung: abwarten bis
      ROCKNIX liefert ODER optional über den Updater laden und über /usr/bin/dsperate einhängen (Lizenz klären,
      ROCKNIX-Startoptionen + CC-Annahmen .auto.dss/.N.dss/dsperate.ini prüfen, dynamisch vs. statisch).
      Vulkan + panfrost: betrifft nur die Ausgabe/Skalierung; PanVK nennt Vulkan 1.3 für G52 (Konformität unklar).
      Nur messen hilft: gleiche Stelle, FPS, gpu_present an/aus × panfrost/libmali (zusammen mit dem Treiber-Vergleich).
- [ ] **Beobachten: advanced_drastic** (https://github.com/trngaje/advanced_drastic, vorerst nur im Blick behalten – Stand 24.10.2026: 370f053) – Update 23./24.10.2026: **RG DS mit
      zwei eigenen Fenstern** (vorher ein schwebendes Fenster + Sway-Zeilen; Skript kannte auch „RG DS Plus“).
      LD_PRELOAD-Hook für DraStic v2522, eigenes Menü (Auto-Speichern/Laden mit Slot, FPS, Save/Load-Taste, Cheats,
      falsches Mikrofon). Installer ersetzt den DraStic-Starter (eigenes drastic_v2522, eigenes LD_PRELOAD statt
      libdrastouch.so, beendet gptokeyb), Sicherung drastic.tar.gz + Deinstallation. **Keine Lizenz** → nicht mitliefern.
      Konflikte mit RDS: `fullscreen enable global` (Gameswitcher/Schnellwechsel/Sicherheitsnetz) und `touch_map`
      **Test Plus 26.10.:** nicht unterstützt – Bibliothek kennt nur QUIRK „Anbernic RG DS“, kein Layout für 2048x768
      (resources/bg/…/layout.json fehlt) → pRenderer=(nil), kein Bild, Watchdog/Segfault. Zurückgestellt (eigene Sicherung
      rds-drastic-vor-advanced.tar.gz). Prozess heißt drastic_v2522 → CC erkennt DraStic am Namen (anpassen, falls genutzt).
      **Konflikt v15.3.3:** NDS-Mikrofonerkennung an (DSHOOK_MIC_THRESH>0) → start_drastic.sh lädt libdrastouch auch in
      den Shell-Starter von advanced_drastic → Mikrofon-Init ohne SDL → Segfault vor dem Start. Mit advanced_drastic
      Mikrofon aus; Installer müsste advanced_drastic erkennen (drastic = Skript, drastic_v2522 vorhanden) und auslassen.
      **Läuft auf dem Plus (26.10. 13:20)** mit eigenem Layout resources/bg/2048x768/layout.json (basic 1024×768 je
      Bildschirm, pixel 3× mit Rand) und Mikrofonerkennung aus: Bild richtig, Touch richtig, Tauschen (Kachel/F8),
      Anbernic+X/Kachel Menü, Anbernic+R2/L2, Savestate laden, L3-Mikrofon (Rollen-Taste), Beenden + ES-Navigation ok.
      Pusten fehlt (ROCKNIX-Erkennung aus) → Idee: CC hört das Mikrofon selbst ab (arecord, Pegel über Grundrauschen →
      Rollen-Taste halten) – geht mit beiden DraStic-Varianten, ROCKNIX-Erkennung bleibt aus. Offen: Menü-Optik, Leistung.
      **Beenden 26.10.:** advanced_drastic ignoriert SIGTERM; CC erkannte mal Starter („drastic“, Skript), mal Programm
      (drastic_v2522) → Starter beendet, Programm lief weiter (zweites Fenster, Mikrofon belegt, Bild verzerrt, Speichern
      ewig). Jetzt: Prozessbaum durchsuchen, Quit-Taste F7 (CONTROL_INDEX_QUIT=320), Rückfall SIGTERM/SIGKILL, dann
      Starter. Offen: Neu starten, Schnellwechsel (SIGSTOP) und Gameswitcher mit advanced_drastic prüfen; „Enable Device
      Microphone“ (eigenes echtes Mikrofon) – Kerzen reagierten nicht (evtl. wegen der hängenden zweiten Instanz) → neu testen.
      **26.10. 13:53:** CC hört selbst ab (mic_watch, Schwelle 0,15) → mit advanced_drastic (Device Microphone = no)
      gehen Kerzen per Pusten UND L3 aus. Beenden über F7, Auto-Laden, Speichern ok. Offen: normales DraStic mit
      mic_watch, RG DS, Fehlauslösungen (Spielton/Reden), Neu starten/Schnellwechsel/Gameswitcher mit advanced_drastic.
      Messung: Pusten 1,9 s / Pegel 0,49–0,50 / ZCR 0,03–0,04; Reden 0,18–0,27 (laut 0,46, ZCR 0,057); Klatschen 0,1–0,25 s.
      Klang trennt nicht → Schwelle 0,30, Grundrauschen nur in Ruhe nachführen, ab 3 lauten Stücken (0,15 s).
      **RG DS 26.10.:** eingebautes Mikrofon liefert nur Rauschen (still/pusten/reden gleich, ~0,025/max 0,12; arecord vom
      „Built-in Audio Microphone“, Gain voll). Ursache vermutlich ROCKNIX-Gerätebaum: rk3568-anbernic-rg-ds.dts hat
      KEINEN rk817-codec-Knoten mit `rockchip,mic-in-differential` – der RG DS Plus hat ihn (dort geht das Mikrofon).
      → Hinweis/Fehlerbericht an ROCKNIX (Device Tree RG DS). Bis dahin auf dem RG DS nur L3.
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

## ROCKNIX-Nightly 20261026 (next) – Prüfung RG DS Plus (26.10. abends, neue SD-Karte)
**Entscheidung 26.10. 21:30: auf den nächsten stabilen ROCKNIX-Release warten.** Zusammenfassung:
docs/rocknix-nightly-inputplumber.md · Umbau als Test auf Branch `nightly` (kein Release).
- [ ] **InputPlumber** ersetzt `retrogame_joypad`: virtueller **DualSense** (uhid, Sysfs `/sys/devices/virtual/misc/uhid/…`,
      Name „Sony Interactive Entertainment DualSense Wireless Controller“), Quellgeräte versteckt (HIDE_DEVICES_FROM_ROOT=1).
      Tasten gleich (304,305,307,308,310–318; Anbernic = 316, L3 = 317), aber **Steuerkreuz = ABS_HAT0X/Y (16/17)**,
      **L2/R2 = ABS 2/5 (0–255)**, Sticks 0–255 (Mitte ~127). → CC: eingebautes Gamepad am uhid-Pfad erkennen (nicht als
      externen Controller), Hat-Steuerkreuz + Achsen 0–255, Tasten einspeisen prüfen, RetroArch-/DSperate-Tabellen.
- [ ] **Home-Taste tot (ROCKNIX-Fehler):** anbernic_rgds.yaml `BTN_BACK → gamepad: button: KeyF1` → „Invalid or
      unimplemented button: KeyF1“. Richtig `keyboard: KeyF1` (wie anbernic_gen1/arc). Versuch: tools/rds-inputplumber-fix.sh
      (Override in /etc/inputplumber/capability_maps.d). Danach CC: Home = KEY_F1 (59) auf „InputPlumber Keyboard“.
      Fehlerbericht an ROCKNIX. **Getestet 26.10.: Home → KEY 59 auf „InputPlumber Keyboard“ ✓** (Bind-Mount, /etc ist ro).
- [ ] **Phantom-Stick RG DS Plus unter InputPlumber:** RX = -Y, RY = X → als rechter Stick weitergegeben (ES-Stick falsch).
      Bisherige Abhilfe (rightanalog aus es_input für retrogame_joypad) greift nicht mehr. „Right Stick“ aus der Zuordnung
      entfernen reicht NICHT (RX/RY dann Standard-Übersetzung, RY = -X). Versuch 2: InputPlumber-Filter
      `events: exclude: [Gamepad:Axis:RightStick]` am adc-joystick in 02-rg-ds-plus.yaml (tools/rds-inputplumber-fix.sh).
      **Getestet 26.10. 20:10: RX/RY bleiben in Ruhe, linker Stick sauber ✓.** Offen: dauerhaft beim Start (vor InputPlumber).
- [ ] **Stick RG DS Plus „träge“ unter InputPlumber (26.10.):** adc-joystick meldet 15..940 (Mitte 477), Ruhe X ~445 / Y ~511,
      erreicht X 136..926 / Y 105..911 → nach InputPlumber Mitte ~118 statt 128, Ausschlag 74–80 %, ES-Schwelle ~70 %.
      (Früher kalibrierte der ROCKNIX-Joypad-Treiber die Mitte.) Versuch: tools/rds-stickcal.sh (EVIOCSABS Min/Max um die
      Ruhelage, InputPlumber neu starten). InputPlumber kennt nur deadzone/quadratic_scaling, keine Mitte.
      **Getestet 26.10. 20:25: voller Ausschlag 0..255, ES fühlt sich besser an ✓.** Ruhelage schwankt (flacher Stick wie
      PS Vita, X 409..460) → Mitte = Mittel aus 4 Richtungen. Offen: beim Start anwenden (Werte aus rds-stickcal.txt, vor
      InputPlumber), ggf. im CC neu kalibrieren.
- [ ] Sonst neu: start_drastic.sh `kill -9 $(pidof gptokeyb)`, DSHOOK_WINDOW_SIZE, DSperate 3.0.5, ES 26.10.,
      CPU bis 1992 MHz, DraStic-Grundbelegung MENU a=1035 (L3!) b=1034 – mit unserem L3-Mikrofon abgleichen.
- [x] **27.10.: Plus zurück auf ROCKNIX-DraStic** (advanced_drastic zu fehlerhaft): tools/advanced-drastic/rds-adv-zurueck.sh
      (entfernt nur advanced-Dateien, Starter aus drastic.tar.gz, drastic.cfg/Spielstände/BIOS/Pust-Geräusch bleiben) +
      rds-adv-cfg.sh (drastic.cfg aus der Fassung vor advanced + heutige Tasten/RDS-Werte). Danach startete DraStic auf
      dem Plus mehrmals als kleines Fenster (früher selten) → CC-Wächter (drastic_fullscreen_guard): prüft 20 s die
      Fensterbreite (normal deckt DraStic beide Bildschirme ab, auch mit fullscreen_mode 0), zweimal zu klein →
      „fullscreen enable global“. Test 09:02: zwei Starts ohne Eingriff, Bild korrekt. Kommt ins nächste Release.
- [x] **27.10. Leistung Plus (Zelda PH, tools/rds-leistung.sh):** DraStic libmali 61 % CPU gesamt / Panfrost 54 %,
      DSperate 48 % / 50 % (DSperate hängt an einem Kern: 80–89 %), Temperatur ≤ 56 °C, ≥ 380 MB RAM frei, kein Swap.
      Prozesse bei DraStic: drastic ~135 %, pipewire ~13 %, sway ~8 %, gptokeyb ~5 %, CC 9,4 % → 5,4 % (mic_watch:
      Spielprüfung alle 3 s statt 1 s, Pegel aus jedem 4. Wert; Pusten weiter ✓). arecord-Zombie behoben (wait).
      NSMB 2 min libmali: DraStic 48 % gesamt / Emulator 105 % (Kerne gleichmäßig ~49 %, ≤ 58 °C) · DSperate 44 % /
      133 % (Kerne 60/27/51/38 %, ≤ 55 °C). Beide mit viel Reserve.

## Idee (27.10., nur theoretisch): Pokémon tauschen (GB/GBC/GBA) mit beiden Bildschirmen
- **GB/GBC, ein Gerät:** zwei RetroArch-Instanzen mit **Gambatte**, je ein Spiel/Spielstand, oben + unten im Vollbild;
  Link über Core-Option „Game Link Mode“ Network Server/Client (`gambatte_gb_link_mode`, Port 56400,
  `…server_ip_*` = 127.000.000.001). Normale Gambatte-Spielstände (kein Kopieren). Gleiches Verfahren zwischen RG DS
  und Plus (Server-IP = anderes Gerät), ohne RA-Netplay.
- **Steuerung:** beide Instanzen lesen dasselbe Gamepad → `input_joypad_driver = sdl2` nur für diese Instanzen
  (SDL liefert Gamepad nur ans Fenster mit Fokus – testen), Fokus per **L3** (frei bei GB/GBA; CC fängt L3 schon ab)
  bzw. Touch (RG DS) und/oder Kachel „Tauschen“ wie DraStic (Fenster zwischen den Bildschirmen tauschen, Fokus oben).
  Rückfall: CC beansprucht das Gamepad und leitet an ein virtuelles Gamepad der zweiten Instanz weiter.
- **GBA:** gpSP „Link Cable Connectivity = GBA Wireless Adapter“ über RA-Netplay (RA ≥ 1.18), nur Feuerrot/
  Blattgrün/Smaragd; zwei Geräte. Unterer Bildschirm: Verbindungsstatus im CC.
- Vorbild: Onion OS „Easy Netplay – Pokémon“ (TGB Dual-Subsystem + Netplay + Spielstand per FTP; GBA über gpSP).
  Onion = GPL → nur das Verfahren nachbauen, Credit in CREDITS.md. Alternative TGB Dual (beide GBs in einem Bild).
- Erster Schritt: Core-Check (gambatte/tgbdual/gpsp, RA-Version, input_joypad_driver), dann Test zwei Instanzen.
- [x] **27.10. Artwork Manager: Listenvorschau** – Spieleliste zeigt oben die vorhandenen Artworks des gewählten Spiels als
      Mix (Image/Boxart/Cartridge, ✓ vorhanden / – fehlt), ohne Wartezeit (Hintergrund-Lader, data/cache/liste mit
      Prüfsumme, Bildablage wird freigegeben). Getestet auf dem Gerät ✓ – kommt ins nächste Release.
