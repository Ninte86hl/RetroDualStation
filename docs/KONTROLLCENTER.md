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
  | DSperate | testen | Bildschirmfoto vor dem Beenden |

## Etappen
1. Grundversion: Seite 1 + Wisch-Gerüst + Home kurz/lang + Hell/Dunkel + Akzentfarbe
2. Seite 2: Spiel-Buttons und Spickzettel
3. Seite 3: RetroAchievements
4. RetroArch-Touchmenü ersetzen, Aufnahme in den Installer
5. Gameswitcher (nutzt Home-Taste, Speichern per Tastendruck, Screenshot und RetroArch-Steuerung aus 1–2)
