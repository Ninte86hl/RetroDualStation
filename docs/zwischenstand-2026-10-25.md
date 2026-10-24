# Zwischenstand 25.10.2026 (Übergabe für den nächsten Chat)

Repo `Ninte86hl/RetroDualStation`, Arbeitszweig **kontrollcenter** (main = Release). Alles committet und gepusht.
Geräte: RG DS Plus `root@192.168.178.80`, RG DS `root@192.168.178.21`. PC-Repo: `~/RetroDualStation/retrodualstation`.
Übertragen: `scp controlcenter/rds_cc.py root@<ip>:/storage/.config/retrodualstation/controlcenter/ && ssh root@<ip> 'systemctl restart essway'`

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

## Gerade in Arbeit (noch nicht abgenommen)
- **Laden-Menü**: 4 Spalten, Slot 1–9 + Kachel **„Automatisch“** (Platz 0, Schloss, nicht lösch-/speicherbar,
  Bild notfalls aus dem Gameswitcher). Letzte Reihe: Slot 9 · Lücke · Fläche in Theme-Farbe (bündig mit Spalte
  Slot 8) mit „Automatischer / Speicherpunkt“ rechtsbündig neben der eingerückten Automatisch-Kachel.
  Speichern bleibt 3×3. Letzter Commit `f6add12` – Michel prüft die Optik (Screenshot:
  `grim -o DSI-1 /storage/laden.png`). Laden aus „Automatisch“ funktioniert bei allen drei Emulatoren.

## Offen (docs/TODO.md)
- Schnellwechsel: Schalter im CC + Standard an/aus.
- Bluetooth-Agent vervielfacht sich bei jedem ES-Neustart (15× ≈ 380 MB).
- Savestates-Übergang für bestehende Nutzer (eigene Stände auf Platz 0, v. a. DSperate → freien Slot; RA `.state9`).
- Installer: DraStic `compress_savestates = 0`.
- DSperate „Neu starten“ (Y) prüfen – Autoload kommt per `--autoload`, nicht aus dsperate.ini.
- RG DS: Slot-/Laden-Ansicht und Auto-Laden noch nicht getestet; `drastic` 0,3 s dort gegenprüfen.
- Optimierungsliste: 2) mehrere Spiele parken auf dem RG DS (über 2 GB frei) · 5) Testskripte in `tools/` aufräumen.
- Wiki/Anleitung (Home-Belegung, Slots 1–9) erst nach Abnahme anpassen.
