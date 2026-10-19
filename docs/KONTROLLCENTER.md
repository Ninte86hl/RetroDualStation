# DualStation Kontrollcenter – Plan

Stand: 19.10.2026 · Status: Planung, noch nichts gebaut

Ein eigenes Kontrollcenter für ROCKNIX DualStation, das **überall** aufrufbar ist
(EmulationStation, RetroArch, DraStic, DSperate …). Es soll DualStation ein
eigenes Alleinstellungsmerkmal geben und das Touchmenü von RetroArch auf dem
unteren Bildschirm ersetzen, damit niemand versehentlich in den
RetroArch-Einstellungen landet.

Entwurf (Mockup, drei Seiten + helle Variante): Design-Artifact
„DualStation Kontrollcenter“ in claude.ai.

## Bedienung

| Aktion | Wirkung |
|---|---|
| **Anbernic-Taste** (allein gedrückt) | Kontrollcenter auf dem **unteren Bildschirm** ein-/ausblenden |
| **Return/Home-Taste** | Gameswitcher ein-/ausblenden (Spielstand speichern, Spiel wechseln, zurück zu ES) |
| Return/Home lang | laufendes Spiel direkt beenden (ohne Switcher) |
| eine der beiden bei ausgeschaltetem unterem Bildschirm | Bildschirm wieder einschalten |

Beide Tasten gibt es am RG DS und am RG DS Plus. Die Anbernic-Taste dient in
Emulatoren auch als Hotkey-Modifikator: das Kontrollcenter öffnet sich nur,
wenn sie **allein** gedrückt und losgelassen wird; als Teil einer
Tastenkombination (z. B. Anbernic + R1) bleibt sie unangetastet.
| Wischen links/rechts oder L1/R1 | Seite wechseln (Punkte unten zeigen die Seite) |
| Steuerkreuz + A | Auswahl ohne Touch |

**Pause:** Beim Öffnen pausiert das laufende Spiel, beim Schließen läuft es an
derselben Stelle weiter.
- RetroArch: Pause-Befehl über die Steuerschnittstelle
- alle anderen (DraStic, DSperate …): Prozess einfrieren/auftauen (SIGSTOP/SIGCONT)
- Speichern/Laden aus Seite 2: Emulator kurz auftauen, Befehl auslösen, wieder einfrieren
- auf dem Gerät testen, ob der Ton beim Einfrieren knackt; sonst während der Pause stummschalten

**Emulator-Tastenkürzel:** Standard **aus**: Speichern, Laden, Vorspulen usw.
laufen nur über das Kontrollcenter, damit Einsteiger keine Kombinationen
versehentlich auslösen (z. B. Spiel ungewollt beendet oder Spielstand
überschrieben). Für erfahrene Nutzer ein Schalter „Tastenkürzel erlauben“;
nur dann zeigt Seite 2 den Spickzettel.
- RetroArch: unproblematisch, die Steuerschnittstelle braucht keine Hotkeys
- DSperate: Tastenkürzel funktionieren und lassen sich in seiner eigenen Tastenbelegung frei anpassen (laut Nutzer) – damit können sie auf eine Belegung gelegt werden, die nur das Kontrollcenter auslöst
- DSperate-Belegung (Fotos vom Gerät, 19.10.2026): Modifier = Funktionstaste;
  Beenden MOD+Start, Pause MOD+West, Vorspulen-Umschalter MOD+R1,
  Speichern MOD+R2, Laden MOD+L2, FPS MOD+North, Mic L3; Slot ±,
  Screenshot, Bildschirm tauschen, Lautstärke, Stumm: unbelegt.
  Jede Aktion hat eine **zweite Belegung „(2)“** und kann auf **Tastatur
  oder Pad** gelegt werden → Plan: das Kontrollcenter belegt die (2)-Plätze
  mit Tastaturtasten, die es am Gerät nicht gibt (z. B. F13–F24), und drückt
  sie über eine virtuelle Tastatur. Die Pad-Kürzel können dann für
  Einsteiger auf NONE.
- DraStic/DSperate: die Knöpfe sollten die Kürzel per virtuellem Tastendruck
  auslösen. Sind die Kürzel abgeschaltet, braucht es einen anderen Weg
  (z. B. Belegung auf eine Taste/Kombination, die nur das virtuelle Gerät
  drücken kann) – auf dem Gerät testen

## Seiten

### 1 · Schnelleinstellungen
- Uhrzeit, Datum; Status: WLAN (Name), Bluetooth (Geräte), Akku (%, lädt)
- „Läuft gerade“: Spiel, System, Emulator, Spielzeit der Sitzung + **Spiel beenden**
- Regler: **Helligkeit oben**, **Helligkeit unten** (getrennt), **Lautstärke**
- **Leistung**: Sparen / Ausgewogen / Leistung (CPU-/GPU-Governor, sofort wirksam;
  später optional „für dieses Spiel merken“)
- Kacheln: WLAN, Bluetooth, **unteren Bildschirm aus** (inkl. Touch aus),
  Ruhemodus
- Sicherheitsnetz: Spielende schaltet den unteren Bildschirm immer wieder ein

### 2 · Spiel (Buttons & Shortcuts)
- Kacheln: Speichern, Laden, Slot −/+, Vorspulen, FPS, Screenshot, Pause,
  Emulator-Menü (auch der bewusste Weg ins RetroArch-Menü)
- Spickzettel: echte Tastenbelegung des laufenden Emulators, aus dessen
  Einstellungsdatei gelesen
- Auslösen: RetroArch über die Netzwerk-Steuerschnittstelle; DraStic und
  DSperate über virtuelle Tastendrücke (bei DraStic auf dem Gerät testen)
- Unterstützung laut Nutzer:

  | | Speichern/Laden | Vorspulen | FPS |
  |---|---|---|---|
  | RetroArch | ✓ | ✓ | ✓ |
  | DraStic | ✓ | ✓ | – |
  | DSperate | ✓ | ✓ | ✓ |

### 3 · RetroAchievements
- Fortschritt (z. B. 12 / 45, Punkte, Balken), zuletzt freigeschaltet, nächste Ziele
- Daten über die RetroAchievements-Web-API mit Benutzername + persönlichem
  Web-API-Schlüssel; Spiel-ID aus RetroArch
- Nur RetroArch-Spiele, braucht WLAN; ohne beides ein kurzer Hinweis statt leerer Seite

## Aussehen

**Freigegebener Entwurf (19.10.2026):** so soll es optisch umgesetzt werden.

| | |
|---|---|
| ![Schnelleinstellungen](kontrollcenter/1-schnelleinstellungen.png) | ![Spiel](kontrollcenter/2-spiel.png) |
| 1 · Schnelleinstellungen | 2 · Spiel |
| ![Erfolge](kontrollcenter/3-erfolge.png) | ![Gameswitcher](kontrollcenter/gameswitcher.png) |
| 3 · RetroAchievements | Gameswitcher |

- **Hell / Dunkel** (Standard Dunkel), umschaltbar im Kontrollcenter, wird gemerkt
- **Akzentfarben** wählbar (fester Bestandteil, nicht nur Bonus): Farbe für
  aktive Kacheln, Regler und Auswahl
- Keine Theme-Einbindung (bewusst entschieden: zu viel Pflegeaufwand)
- Stil an canvas-ds angelehnt: dunkle halbtransparente Kästen, runde Ecken,
  graue Auswahlleiste

## Technik (zu klären auf dem Gerät)
- Hintergrunddienst liest die Home-Taste (kurz/lang) über evdev
- Overlay über Vollbild-Spielen: Sway-Overlay-Ebene (wlr-layer-shell) nötig –
  prüfen, welche Bibliotheken ROCKNIX mitbringt
- Helligkeit: /sys/class/backlight · Lautstärke: wpctl/amixer ·
  WLAN/BT: connmanctl/iwctl/bluetoothctl · Leistung: cpufreq/devfreq-Governor ·
  Bildschirm aus: swaymsg output … power off
- RetroArch-Touchmenü in der DualStation-Einrichtung abschalten
  (Stock ROCKNIX im Single-Modus bleibt unverändert)
- Alter „Home-Exit-Helfer“ vom RG DS (ROCKNIXDS) als Vorlage für Home lang

Befehle zur Bestandsaufnahme (ein RetroArch-Spiel läuft):

```
ssh root@<IP> "ps -eo pid,args | grep -v '\[' | grep -vE 'ps -eo|grep'"
ssh root@<IP> "grep -E 'Name|Handlers' /proc/bus/input/devices"
ssh root@<IP> "ls /usr/lib | grep -iE 'wayland|layer|SDL2|cairo|gtk' ; which swaynag wpctl amixer iwctl connmanctl bluetoothctl"
ssh root@<IP> "cat /sys/devices/system/cpu/cpufreq/policy*/scaling_available_governors; ls /sys/class/devfreq/; cat /sys/class/devfreq/*/available_governors"
```

## Gameswitcher (später)

Optische Spielerei mit Mehrwert: **es läuft immer nur ein Spiel**, es werden
keine Spiele parallel im Hintergrund gehalten.

- Home lang: Screenshot → Spielstand automatisch speichern → Emulator sauber beenden
- Unterer Bildschirm: zuletzt gespielte Spiele als Karten mit ihrem letzten
  Screenshot, Wischen zum Blättern
- Antippen: Spiel über die ES-Schnittstelle starten, Spielstand automatisch laden
- Karte „Zurück zu ES / nur beenden“
- Zu klären pro Emulator:

  | | Auto speichern/laden | Screenshot |
  |---|---|---|
  | RetroArch | eingebaut (Auto-Savestate) | Vorschaubild zum Spielstand |
  | DraStic | testen (virtueller Tastendruck, beim Start laden) | Bildschirmfoto vor dem Beenden |
  | DSperate | eingebaut (Einstellung für automatisches Speichern/Laden) | Bildschirmfoto vor dem Beenden |

## Etappen
1. Grundversion: Seite 1 + Wisch-Gerüst + Home kurz/lang + Hell/Dunkel + Akzentfarbe
2. Seite 2: Spiel-Buttons und Spickzettel
3. Seite 3: RetroAchievements
4. RetroArch-Touchmenü ersetzen, Aufnahme in den Installer
5. Gameswitcher (nutzt Home-Taste, Speichern per Tastendruck, Screenshot und RetroArch-Steuerung aus 1–2)

## DraStic-Einstellungen (nach dem Kontrollcenter)

DraStic ist nicht quelloffen, sein Pausemenü ist auf dem RG DS Plus sehr klein.
1. Schneller Gewinn: das vergrößerte Pausemenü vom RG DS übernehmen
   (`librgdsmenu.so` per LD_PRELOAD, 2,2×).
2. Eigene Einstellungsoberfläche im DSperate-Stil, die DraStics Textdatei
   (`drastic.cfg`) liest und schreibt:
   - Kategorien Emulation, Bild, Layout, Tasten; große Schrift, Touch
   - Bedeutung und erlaubte Werte jedes Eintrags einmalig festhalten
     (Tastencodes → lesbare Tastennamen)
   - nur schreiben, wenn DraStic nicht läuft (DraStic speichert beim Beenden
     selbst und würde Änderungen überschreiben); Sicherung vor der ersten Änderung
   - Änderungen gelten beim nächsten Start; mit dem Gameswitcher kaum spürbar
   - Fundort: `find /storage -name 'drastic.cfg'`

## Bestandsaufnahme RG DS Plus (19.10.2026)

**Tasten**
- Anbernic-Taste: `retrogame_joypad` (`/dev/input/event6`), `BTN_MODE` (316)
- Return/Home-Taste: `adc-keys-back` (`/dev/input/event2`), `BTN_Z` (309)
- ROCKNIX-Tastendienst `/usr/bin/input_sense` (Bash + `evtest` je Gerät): Lautstärke,
  Power, Deckel, Hotkeys über Funktionstaste (`key.function.a` …, in system.cfg
  überschreibbar). Unser Dienst muss sich mit ihm vertragen (Anbernic-Taste allein
  vs. als Modifikator).

**Grafik & System**
- vorhanden: SDL2 (+ image, ttf, mixer, gfx), GTK3, Cairo, Qt6 Wayland, Wayland-Client;
  keine Layer-Shell-Bibliothek
- Ton `wpctl`/`amixer` (PipeWire) · WLAN `iwd`/`iwctl` + NetworkManager ·
  Bluetooth `bluetoothctl` · Benachrichtigungen `mako`
- Leistung: CPU `ondemand powersave performance schedutil`, GPU (`fde60000.gpu`)
  `powersave performance simple_ondemand` → Sparen = powersave/powersave,
  Ausgewogen = schedutil/simple_ondemand, Leistung = performance/performance

**Das RetroArch-Touchmenü: „lowerdeck“** (`/usr/share/lowerdeck`, GPL-2.0-or-later)
- Python 3 + SDL2 über ctypes (keine Zusatzpakete), Fenster per Sway-Regel
  (`app_id` „lowerdeck“) auf den unteren Bildschirm
- Gestartet von `runemu.sh` mit `--rom --core --platform --ra-pid`
- Steuert RetroArch über UDP 55355 (MENU_TOGGLE, SAVE_STATE_SLOT, LOAD_STATE_SLOT,
  GET_CONFIG_PARAM …), Savestate-Vorschaubilder, Helligkeitsregler, Abdunkeln bei Leerlauf
- **RetroAchievements ohne API-Schlüssel:** `ra_proxy.py` sitzt als lokaler Proxy zwischen
  RetroArch und retroachievements.org (`cheevos_custom_host`) und liest die Daten mit
- **Entscheidung:** Eigenentwicklung, kein Code aus lowerdeck. Öffentlich dokumentierte
  Schnittstellen (RetroArch-Netzwerkbefehle UDP 55355, SDL2, sysfs, wpctl …) nutzen wir
  selbst; lowerdeck zeigt nur, dass der Weg auf dem Gerät funktioniert. Im Dual-Modus
  wird lowerdeck abgeschaltet und durch das Kontrollcenter ersetzt. Bei Single-Screen-
  Spielen ist der untere Bildschirm frei – kein Overlay nötig; nur bei DraStic (beide
  Bildschirme) muss sich das Kontrollcenter darüberlegen.

**DraStic** (`/storage/.config/drastic/config/drastic.cfg`)
- Menü, Speichern, Laden, Vorspulen sind auf Joypad-Tasten belegt (`controls_b`,
  Codes 1035/1031/1030/1036); Bildschirme tauschen und Beenden unbelegt
- `savestate_snapshot = 1`: DraStic legt Vorschaubilder zu Spielständen ab (Gameswitcher)
- `controls_a` = zweite Belegung; ob DraStic dort virtuelle Tastendrücke annimmt, testen

## Overlay-Test (19.10.2026) – Bauweise steht fest

`swaynag -o DSI-1 -y overlay` (Wayland-Layer-Shell, Ebene „overlay“) erscheint auf dem
**unteren Bildschirm (DSI-1)** über **ES, RetroArch, DraStic und DSperate**, ohne die
Emulation zu stören.

**Bauweise des Kontrollcenters**
- eigenes Programm in Python 3 (auf ROCKNIX vorhanden, nichts zu kompilieren)
- Anzeige als Layer-Shell-Fläche „overlay“ auf DSI-1, direkt über `libwayland-client`
  (ctypes); Zeichnen mit Cairo (`libcairo`)
- Tasten direkt über evdev: Anbernic `BTN_MODE` (event „retrogame_joypad“),
  Return/Home `BTN_Z` (event „adc-keys-back“); solange das Kontrollcenter offen ist,
  wird das Joypad exklusiv übernommen (EVIOCGRAB), damit Spiel/ES keine Eingaben bekommen
- Wayland-Umgebung: `XDG_RUNTIME_DIR=/var/run/0-runtime-dir`, `WAYLAND_DISPLAY=wayland-1`

## Prototyp 0.1 getestet (19.10.2026)

`controlcenter/rds_cc.py`: Anbernic-Taste öffnet das Kontrollcenter, Home-Taste den
Gameswitcher-Platzhalter, jeweils auf DSI-1 über ES, RetroArch, DraStic und DSperate.
Während der Anzeige erreichen weder Tasten noch Touch das Spiel bzw. ES.
Behoben: doppeltes Übernehmen des Joypads beim direkten Wechsel zwischen den Ansichten.

## Prototyp 0.2 (19.10.2026)

Seite „Schnelleinstellungen“ nach dem freigegebenen Entwurf, Seiten 2/3 und
Gameswitcher noch Platzhalter.
- Touch auf der eigenen Fläche (wl_seat/wl_touch): Regler ziehen, Antippen, Wischen
- Steuerkreuz hoch/runter = Zeile, links/rechts = Wert/Auswahl, A = Kachel, B = schließen, L1/R1 = Seite
- Helligkeit oben/unten (`/sys/class/backlight`, Zuordnung per Konfiguration änderbar),
  Lautstärke (`wpctl`), Leistung (CPU-/GPU-Governor), WLAN/Bluetooth an/aus,
  Status WLAN-Name, Bluetooth-Geräte, Akku, „Läuft gerade“ aus der Prozessliste
- Hell/Dunkel und Akzentfarbe über `/storage/.config/retrodualstation/controlcenter.json`
  (Auswahl in der Oberfläche folgt)
- Noch nicht: Pause, Spiel beenden, unterer Screen aus, Ruhemodus

## Prototyp 0.3/0.4 (19.10.2026)

- Touch direkt vom Touchscreen (`Goodix Capacitive TouchScreen`, event1, 1024×768,
  ohne Drehung); Sway meldet am Seat nur „Tastatur“, daher kein Wayland-Touch
- Helligkeit: `backlight1` = oben, `backlight0` = unten
- WLAN wie ROCKNIX: `set_setting wifi.enabled`, `wifictl enable|disable` (nur rfkill),
  danach `wifictl connect`; Status über `rfkill`
- Bluetooth wie ROCKNIX: Dienste `bluetooth` + `bluetooth-agent` starten/stoppen,
  `set_setting controllers.bluetooth.enabled`
- ES liest `system.cfg` nur beim Start → ES-Menü zeigt Änderungen erst nach Neustart (To-do)
- 0.4: Pause (RetroArch per `GET_STATUS`/`PAUSE_TOGGLE` über UDP 55355, sonst SIGSTOP/SIGCONT),
  Hell/Dunkel + Akzentfarbe oben links neben den Status-Pillen (gespeichert in
  `controlcenter.json`), Autostart-Dienst `controlcenter/rds-controlcenter.service`

## Prototyp 0.5 (19.10.2026)

- Akzentfarbe für Regler, Leistungsmodus und Kacheln; „an“ = volle Akzentfarbe,
  „aus“ = leicht eingefärbt (Wunsch des Nutzers)
- Untermenüs über „›“ auf der WLAN-/Bluetooth-Kachel (Gamepad: X/Y):
  - WLAN: Netze suchen (`nmcli dev wifi rescan/list`), gespeicherte Netze verbinden
    (setzt auch `wifi.ssid`/`wifi.key` wie ROCKNIX), offene Netze verbinden, trennen, vergessen;
    gesicherte neue Netze brauchen die Bildschirmtastatur (nächster Schritt)
  - Bluetooth: 30 s suchen, koppeln (pair + trust + connect), verbinden, trennen, entfernen
  - Abfragen laufen im Hintergrund, die Oberfläche bleibt bedienbar

## Prototyp 0.6 (19.10.2026)

Eigene Bildschirmtastatur (die von ES lässt sich außerhalb von ES nicht nutzen):
QWERTZ mit ä/ö/ü/ß, Umschalten (einmal/dauerhaft), Zeichen-Ebene „?123“, Passwort
zeigen/verbergen, Akzentfarbe. Bedienung per Touch **und** Gamepad: Steuerkreuz + A,
B = löschen (bei leerem Feld abbrechen), L1 = Groß, R1 = ?123, Select = zeigen,
Start = OK, **linker Stick = Cursor links/rechts** (Idee des Nutzers), Antippen im
Textfeld setzt den Cursor. Erster Einsatz: Passwort für neue WLAN-Netze
(`nmcli dev wifi connect … password …`, dann `wifi.ssid`/`wifi.key` wie ROCKNIX).
Sticks werden nicht mehr als Tastendruck gewertet (Stick-Drift störte sonst die Anbernic-Taste).

## Prototyp 0.7 (19.10.2026)

Tastatur wie am Handy (Wunsch des Nutzers): 10 Spalten, Umlaute und Sonderformen per
**langem Drücken** (Touch: halten, ziehen, loslassen; Gamepad: A halten, links/rechts,
A einfügen, B schließen); wichtigste Variante klein in der Tastenecke.
Layout **QWERTZ bei deutscher Systemsprache** (`system.language` in `system.cfg`),
sonst QWERTY; fest einstellbar über `"keyboard"` in `controlcenter.json`.

## Ideen für später (19.10.2026)

- **Mini-Power-Menü** (wie Android): Ausschalten, Neustart, Ruhemodus, ES neu starten;
  große Knöpfe, Rückfrage vor dem Ausführen; läuft ein Spiel, wird vorher gespeichert
  bzw. sauber beendet.
  **Aufruf über die Ein/Aus-Taste** – entschieden (19.10.2026): **kurz drücken = Power-Menü**,
  weil das RG DS (Plus) klappbar ist und beim Zuklappen über den Hall-Sensor
  (`gpio-keys-hall`, event4 → `rocknix-fake-suspend lid close/open`) ohnehin schläft.
  „Ruhemodus“ ist der erste Knopf im Menü (z. B. aufgeklappt am Ladekabel). Hintergrund:
  - ROCKNIX heute: `input_sense` liest `rk805 pwrkey` (event0) per evtest und ruft schon
    beim Drücken `/usr/bin/rocknix-fake-suspend power` (Ruhemodus) auf;
    langes Halten (6–10 s) = harte Abschaltung durch den Power-Chip (bleibt als Notaus)
  - Umsetzung: unser Dienst übernimmt `rk805 pwrkey` exklusiv (EVIOCGRAB); kurz drücken
    öffnet das Power-Menü, „Ruhemodus“ dort ruft `rocknix-fake-suspend power` auf
  - Zuklappen: Pause bleibt bis zum Aufklappen bestehen; „Unterer Screen aus“ danach
    beibehalten bzw. bewusst wieder einschalten (ROCKNIX schaltet beim Aufklappen die
    Beleuchtung wieder an)
  - Sicherheitsnetz: endet unser Dienst, gibt der Kernel die Taste frei → ROCKNIX wie gewohnt
- **ES-Schnittstelle** `http://localhost:1234/runningGame` (200 = Spiel läuft, 201 = keins;
  nutzt ROCKNIX selbst in `rocknix-fake-suspend`) → für „Läuft gerade“ und den Gameswitcher
- **Log-Manager**: die wichtigsten Logs (Kontrollcenter, ES, RetroArch, DraStic,
  Systemjournal) lesbar anzeigen; „Fehlerbericht erstellen“ sammelt sie mit Version und
  Gerätedaten in eine Datei, die Nutzer ins GitHub-Issue hängen können
  (WLAN-Passwörter und andere Zugangsdaten werden vorher entfernt)

**Pause getestet (19.10.2026):** RetroArch (Steuerschnittstelle), DraStic und DSperate
(Einfrieren) halten an und laufen mit Bild und Ton weiter – über Kontrollcenter und Gameswitcher.

## Prototyp 0.8 (19.10.2026)

Test 0.7 (Nutzer): Tastatur komplett ok (Haltezeit angenehm), WLAN-Liste/Suche ok,
neues WLAN mit Passwort verbunden. Bluetooth: Controller gefunden, Koppeln des
„8BitDo Ultimate 3-mode for Xbox“ schlug fehl.

- Listen scrollen mit dem Finger (pixelgenau, Scrollbalken), Gamepad hält den Fokus sichtbar
- WLAN: gespeicherte Verbindungen über ihre **SSID** erkannt (Verbindungsname kann abweichen,
  z. B. Hotspot) → stehen oben mit „Verbinden“; gespeicherte, aber ferne Netze unten
  („nicht in Reichweite“, nur „Vergessen“). Verbinden: `nmcli connection up`, sonst bei
  ROCKNIX-Standardnetz `wifictl connect`
- **Bluetooth jetzt über ROCKNIX' eigenen Weg** (wie das ES-Menü): Suche über den
  Bluetooth-Helfer (`/run/bt_discovery_control` start/stop), Koppeln mit
  `rocknix-bluetooth trust <MAC>` (Helfer koppelt, vertraut, verbindet mit Wiederholungen
  und **sichert die Kopplung** für den nächsten Start), Verbinden/Trennen/Entfernen und
  Ein/Aus ebenfalls über `rocknix-bluetooth`; Statusmeldungen des Helfers aus `/run/bt_status`

**Vergleichstest ES (19.10.2026):** Koppeln des 8BitDo Ultimate 3-mode Xbox über das ES-Menü
klappt (Helfer-Log: Pairing → Trusting → Connected successfully). Treiber ok; Ursache war der
alte CC-Weg (eigenes `bluetoothctl pair`). 0.8 nutzt denselben Weg wie ES.

**Test 0.8.1 (19.10.2026):** Entfernen, Suchen und Koppeln des 8BitDo im CC funktionieren.
Nach „Trennen“ verband er sich sofort neu → 0.8.2: Suche stoppen und `/run/bt_device`
löschen bei Trennen/Entfernen und beim Verlassen des Untermenüs. Ein gekoppelter,
eingeschalteter Controller verbindet sich trotzdem von selbst wieder (normales
Bluetooth-Verhalten) – Hinweis in der Statuszeile.
**0.8.3:** Entscheidung (19.10.2026): bei verbundenen Controllern (Gerätetyp `input-*`) kein
„Trennen“, nur „Entfernen“ – Controller werden durch Ausschalten getrennt; Audio-Geräte behalten „Trennen“.
**0.8.4:** Suchknopf „Suchen“ → „Sucht …“ → „Aktualisieren“; Listen in Bereiche geteilt
(Bluetooth: Gekoppelte / Gefundene Geräte, WLAN: Gespeicherte / Weitere Netze), eigene
Geräte und Netze bleiben immer oben; Überschriften werden beim Navigieren übersprungen.

## Prototyp 0.9 (19.10.2026)

- **Externe Controller** (Test: „8BitDo Ultimate 3mode Xbox“, event7): werden laufend
  erkannt (auch nachträglich verbunden), Home-/Xbox-Taste öffnet/schließt das CC, solange
  das CC offen ist, gehören sie nur dem CC (vorher navigierte ES dahinter mit).
  Bedienung nach Xbox-Art (A unten = bestätigen, B rechts = zurück). Analoge Achsen und
  Trigger zählen nie als Tastendruck.
- Optik (Wunsch des Nutzers): verbundenes WLAN bzw. Bluetooth-Gerät direkt in der Kachel;
  WLAN-/Bluetooth-Pillen entfallen, oben steht „Kontrollcenter“, rechts Akku + Darstellung.
**0.9.1:** Hell-Modus-Symbol = Sonne mit Strahlen (passend zum Mond), Titel „Kontrollcenter“
größer, davor das RDS-Logo (Variante 3 „Verwoben“, Rot · Weiß/Schwarz · Blau, mit Cairo gezeichnet).

**Test 0.9 (19.10.2026):** externer Controller wird erkannt, Xbox-Taste öffnet das CC, ES bleibt
dahinter ruhig, Kacheln zeigen WLAN/Gerät, RetroArch-Menü öffnet nicht zusätzlich. Im Spiel
funktioniert der 8BitDo nicht – auch ohne CC: Spielerzuordnung (ES-Controller-Einstellungen,
nur RetroArch nutzt sie). Außerdem beendet runemu den Bluetooth-Helfer während Spielen.
