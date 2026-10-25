🇬🇧 [English](Files)

# Dateien von RDS

Was RetroDualStation auf dem Gerät anlegt und wofür. Fast alles beginnt mit **`rds-`** – so lässt es sich im
Dateimanager schnell erkennen. **Uninstall RDS** entfernt alles hier Genannte (bis auf das Deinstallations-Log und die
Daten des Artwork Managers) und stellt deine ursprünglichen Einstellungen wieder her. Spiele, Artworks, Spielelisten,
Savestates und Spielstände bleiben immer unberührt.

## Programm – `/storage/rds-install/`

| Datei | Wofür |
|---|---|
| `emulationstation-rgds` | EmulationStation über beide Bildschirme |
| `start-es-dualstation.sh`, `rgds-sway-fix.sh` | starten ES im Dual-Modus und richten Sway dafür ein |
| `es-switch-helper.sh` | wechselt zwischen Dual- und Single-Modus (Theme, Einstellungen, Power-Taste) |
| `uninstall.sh` | Deinstallation |
| `rds-settings.py` | sichert die Originalwerte der Einstellungen, die RDS ändert, und setzt sie zurück |
| `settings-before-rds.json` | diese Originalwerte (je Einstellung) |
| `rds-migrate-savestates.py` | einmaliger Umzug alter Savestates auf Slots 1–9 |
| `rgds-diag.sh`, `diag-*.txt` | Diagnose für Fehlerberichte |
| `es_settings.before-install.cfg`, `bottomscreen.before` | ES-Einstellungen bzw. unterer Bildschirm von vor der ersten Installation |
| `theme.single`, `theme.dual`, `subsets.single`, `subsets.dual`, `quicksystemselect.single` | Theme und Theme-Optionen je Modus |
| `es-switch.log`, `es_settings.last-switch.cfg` | Protokoll und Stand vor dem letzten Moduswechsel |
| `VERSION` | installierte Version |

(Bis v15.1 hieß der Ordner `rgds-test` – ein Update benennt ihn um.)

## Logs – `/storage/`

| Datei | Wofür |
|---|---|
| `rds-install.log` | Installation und Updates |
| `rds-uninstall.log` | Deinstallation – bleibt danach absichtlich liegen |
| `rds-canvas-install.log` | Installer des Themes canvas-ds |

## Kontrollcenter – `/storage/.config/retrodualstation/`

| Datei | Wofür |
|---|---|
| `controlcenter/rds_cc.py`, `controlcenter/tour/` | Kontrollcenter, Gameswitcher, Power-Menü und die Bilder der Tour |
| `controlcenter.json` | deine Einstellungen im CC (Hell/Dunkel, Farbe, Vibration …) |
| `switcher/` | Liste und Bilder des Gameswitchers |
| `screens.cfg` | Bildschirm-Bereiche für ES (vom Installer ermittelt) |
| `lib/` | Pillow (Bildbearbeitung für den Artwork Manager) |
| `fastswitch` | vorhanden = Schnellwechsel an (Schalter oben im CC) |
| `temp-settings.json` | kurz gesetzte Spiel-Einstellungen (Neustart in DSperate), zum Aufräumen |
| `*.done` | Merker „schon erledigt“, damit der Installer Einmaliges nicht wiederholt |

(Dieser Ordner bekommt den Präfix `rds-` mit dem nächsten Build von ES.)

## Sicherungen

| Datei | Wofür |
|---|---|
| `/storage/roms/backup/rds-original-backup.zip` + `.txt` | Notfall-Sicherung deiner Einstellungen von vor RDS (Format der ROCKNIX-Sicherung) mit Anleitung |
| `/storage/.config/rds-backup/rds-original-backup.zip` | dieselbe Sicherung intern – für die automatische Wiederherstellung beim Start |
| `/storage/.config/rds-uninstall.running` | nur während der Deinstallation: bricht sie ab, stellt der nächste Start die Sicherung wieder her |

## Dienste und System – `/storage/.config/`

| Datei | Wofür |
|---|---|
| `system.d/rds-controlcenter.service` | startet das Kontrollcenter mit ES (nur im Dual-Modus) |
| `system.d/rds-resume.service` | schließt das Power-Menü nach dem Aufwachen |
| `system.d/rds-uninstall-guard.service` | Absicherung der Deinstallation (siehe oben) |
| `system.d/essway.service.d/rds-dual.conf` | vorhanden = Dual-Modus (ES startet über RDS) |
| `logind.conf.d/rds-logind-powerkey.conf` | Power-Taste übernimmt im Dual-Modus das Kontrollcenter |
| `sway/config`, `mako/config` | einzelne Zeilen mit „RetroDualStation“ (Tastatur-Geräte, Lautstärke-Anzeige aus) |

## Ports – `/storage/roms/ports/`

| Datei | Wofür |
|---|---|
| `RDS Dual-Screen.sh`, `RDS Single-Screen.sh` | Modus wechseln |
| `RDS Artwork Manager.sh`, `rds-artworkmanager/` | Artwork Manager – Programm und **deine Daten** (Einstellungen, Sicherungen, eigene Bilder) |
| `Uninstall RDS.sh` | Deinstallation |
| `Install RDS.sh`, `.dualstation/` | nur das heruntergeladene Paket – nach der Installation weg; ein neues Paket erscheint als **Update RDS** |
| `images/rds-*.png` | Icons der Einträge |

## Themes – `/storage/.config/emulationstation/themes/`

`canvas-rds` und `dii-ess-aye-rds` – Themes für beide Bildschirme (Namen bleiben, sonst ginge die Theme-Auswahl verloren).

## Neben deinen Spielständen

| Datei | Wofür |
|---|---|
| `roms/savestates/nds/*.dss.png` | Vorschaubilder der Slots für DraStic und DSperate (RetroArch legt seine selbst an) |

## Nur bis zum Neustart – `/tmp/`

`rds-frozen.json` (geparktes Spiel beim Schnellwechsel), `rds-next-launch` (Auftrag an ES), `rds-gs-timing.json`
(Testzeiten), `rds-shot` und weitere `rds-*` für Tests.

## Geänderte Einstellungen (keine eigenen Dateien)

Der Installer ändert einzelne Einträge in `retroarch.cfg`, `drastic.cfg`, `dsperate.ini`, `es_settings.cfg`,
`es_input.cfg` (RG DS Plus) und `system.cfg` – z. B. Kürzel, ausgeblendete Einblendungen, Slot 1 für manuelles Speichern.
Die Originalwerte stehen in `settings-before-rds.json`; die Deinstallation setzt sie zurück.

Technik: [TECHNIK.md](https://github.com/Ninte86hl/RetroDualStation/blob/main/docs/TECHNIK.md)
