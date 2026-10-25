# Zwischenstand 25.10.2026 (Übergabe für den nächsten Chat)

Repo `Ninte86hl/RetroDualStation`, Arbeitszweig **kontrollcenter** (main = Release). Alles committet und gepusht.
Geräte: RG DS Plus `root@192.168.178.80`, RG DS `root@192.168.178.21`. PC-Repo: `~/RetroDualStation/retrodualstation`.
Übertragen: `scp controlcenter/rds_cc.py root@<ip>:/storage/.config/retrodualstation/controlcenter/ && ssh root@<ip> 'systemctl restart essway'`
(Programmordner ab v15.2 `/storage/rds-install`, vorher `/storage/rgds-test`.)

## Arbeitsweise (Michel)
Deutsch, kurz · Befehle vollständig, je ein Block, mit `git pull` · „Einfach und gut steuerbar“, „Sicherheit vor
Funktionsumfang“ · erst testen, dann TODO/Notizen · keine Zugangsdaten zeigen · Community-Tipps in CREDITS.md.

## Heute erledigt und getestet (in docs/releases/v15.2.md)
- **Touch nach DraStic**: Ursache = ROCKNIX-Regel in `/storage/.config/sway/config`
  (`for_window [app_id="drastic"] … map_to_output DSI-2`), nie zurückgesetzt. Fix: `touch_map()` →
  weg von DraStic `input type:touch map_to_output *`, für DraStic Regel nachbilden. Beide Geräte OK.
- **Wechsel weg von DraStic** wieder per ES-Kette (≈4 s statt 8 s), Touch-Zuordnung danach korrigiert.
  Rückfall: `/tmp/rds-gs-timing.json {"chain_drastic": 0}`. DraStic nach Start sicher `fullscreen enable global`.
- **Schnellwechsel** (Opt-in `/storage/.config/retrodualstation/fastswitch`) mit DSperate, DraStic **und RetroArch**:
  Startbefehl wird pro Spiel im Gameswitcher gemerkt (`launch`); geparktes Spiel auf Arbeitsbereich `rdspark`
  (nicht Scratchpad – Vollbild-Fenster wurden dort weiter gezeichnet), erst danach SIGSTOP; vor dem Aufwecken
  `evdev_flush` (pidfd_getfd) gegen nachgespielte Tasten; Zusatzspiel sicher beenden (`fast_end_extra`, nach 3 s hart);
  Beenden außerhalb des Gameswitchers beendet auch den Anker → ES. Rückweg ≈0,5 s. Beide Geräte OK.
- **Home-Taste neu**: kurz = speichern + ES · 2× = Gameswitcher · halten 0,8 s = letzte beiden Spiele tauschen.
- **DraStic Auto-Laden aus ES** (`drastic_watch`/`drastic_autoload`, mit `global.autosave=1`), Ton stumm bis geladen,
  Wartezeit `drastic` 0,3 s (getestet). Gameswitcher-Start 15 s ausgenommen.
- **DraStic `compress_savestates = 0`** auf dem Plus gesetzt → Speichern ≈0,3 s statt 1,8 s.
- **Savestate-Schema**: Platz 0 = automatisch (Gameswitcher, Home kurz, Auto-Laden) bei allen Emulatoren
  (DSperate: eigene `.auto.dss`); Nutzer-Slots **1–9 = Plätze 1–9** (gleiche Nummern wie in den Emulatoren).
  Überschreiben eines belegten Slots fragt nach (Kachel gedämpft in Theme-Farbe, „Überschreiben?“, 2× A/Tippen).
  Savestates auf dem Plus für den Test komplett gelöscht (Spielstände .srm/.sav unberührt). Test bestanden.

## Release v15.2 (25.10.2026, ~03:15) – auf RG DS und RG DS Plus getestet
Prüfliste `docs/test-v15.2-installer.md` vollständig bestanden (Update, Abbruch, Deinstallation, Neuinstallation,
Update RDS, Single-Modus, Funktionen). Danach behoben und getestet: Gameswitcher ohne RDS-Ports, Theme-Optionen je Modus.

## Nachtrag 25.10. nachts (abgenommen)
- **Laden-Menü** fertig (`4dc8b7b`): 4 Spalten – oben links Spiel-Icon (quadratisch, Kachelhöhe, mittig, ohne
  Rahmen, nicht wählbar), dahinter Slot 1–9 (Slot 9 unter Slot 5), letzte Reihe ab Spalte Slot 6 Fläche in
  Theme-Farbe mit „Automatischer Speicherpunkt“ mittig und Kachel „Automatisch“ unter Slot 7. Speichern bleibt 3×3.
- **Bluetooth-Agent** (`034d7f7`): Ursache runemu.sh – `kill "$NPID"` scheitert bei 2 PIDs, danach je Spiel einer mehr.
  CC prüft alle 30 s in /proc und behält nur den neuesten. Getestet auf dem Plus.
- **Schalter Schnellwechsel** (`4dbfd84`): CC oben 4. Symbol (Pfeile), gesperrt solange ein Spiel geparkt ist;
  Installer schaltet ihn einmal je Gerät ein (Merker `fastswitch-default.done`). Getestet auf dem Plus.
- **Single-Modus** (`918af52`): CC-Dienst nur mit Dual-Drop-in, Power-Taste im Single-Modus wieder ROCKNIX (logind
  über es-switch-helper.sh). Noch nicht getestet.
- **Installer/Deinstallation** (`e64cba0` … `95390ef`, noch nicht auf dem Gerät getestet):
  `rds-settings.py` sichert Originalwerte je Einstellung (JSON) und setzt sie zurück; Notfall-ZIP
  `roms/backup/RDS_ORIGINAL_BACKUP.zip` (backuptool-Format, nur beim ersten Mal); bei Fehler sofort eingespielt,
  bei Abbruch per `rds-uninstall-guard.service` beim nächsten Start (Merker `/storage/.config/rds-uninstall.running`);
  saubere Deinstallation bis aufs Log (Artworks, Savestates, Spielstände, AM-Daten bleiben; `*.dss.png` weg);
  Update-Erkennung, Port-Eintrag heißt danach „Update RDS“; Programmordner jetzt **/storage/rds-install**
  (Update benennt `rgds-test` um). **Achtung:** neue `es-switch-helper.sh` nicht mehr per scp in den alten Ordner
  kopieren – erst per Installer updaten.
- **Installer**: DraStic `compress_savestates = 0` (`0038ade`) – offen: laden alte komprimierte Stände noch?

## Offen (docs/TODO.md)
- Savestates-Übergang für bestehende Nutzer (eigene Stände auf Platz 0, v. a. DSperate → freien Slot; RA `.state9`).
- Installer DraStic `compress_savestates = 0`: prüfen, ob alte komprimierte Stände noch laden.
- DSperate „Neu starten“ (Y) prüfen – Autoload kommt per `--autoload`, nicht aus dsperate.ini.
- RG DS: neue Laden-Ansicht und Auto-Laden noch nicht getestet; `drastic` 0,3 s dort gegenprüfen.
- Durchlauf RG DS: Neuinstallation, Update, Deinstallation (Vergleich, Reste), Abbruch-Fall, wieder installieren.
- Optional: Rücksicherung der vorherigen Version beim Update.
- Optimierungsliste: 2) mehrere Spiele parken auf dem RG DS (über 2 GB frei) · 5) Testskripte in `tools/` aufräumen.
- Wiki/Anleitung (Home-Belegung, Slots 1–9) erst nach Abnahme anpassen.
