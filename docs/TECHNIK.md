# RetroDualStation – Technik

🇬🇧 [English](TECHNICAL.md) · [← README](../README.de.md)

## Behobene Probleme mit dii-ess-aye auf dem RG DS Plus

Das sind keine Fehler im Theme selbst. Sie entstehen dadurch, wie das
Original-ES und die Sway-Regeln von ROCKNIX mit einem Fenster von
2048 × 768 umgehen. Dieser Mod behebt sie in EmulationStation und in der
Sway-Einrichtung, damit das Theme wie gedacht funktioniert:

| Problem mit Original-ES / ROCKNIX | Behoben durch |
|---|---|
| Unterer Screen nach der Rückkehr aus einem Spiel aus, alles landet oben | Sway-Regeln (`rgds-sway-fix.sh`) |
| Navigation zwischen den Systemen in der Hauptansicht funktionierte nicht | Sway: globales Vollbild über beide Ausgänge |
| ES-Fenster schrumpfte nach einem Spiel oder Neustart auf einen Screen (1024 × 768) | Sway: globales Vollbild über beide Ausgänge |
| Korrekturen gingen bei jedem Neustart verloren (ROCKNIX schreibt die Sway-Config neu) | `rgds-sway-fix.sh` läuft vor jedem Start |
| Scraper-, Updates-, Downloads- und Theme-Menüs über beide Screens gezogen | ES-Patch (`RGDS_MENU_W`) |
| Info-Meldungen (z. B. „Scraping finished“) über beide Screens verteilt | ES-Patch (`GuiInfoPopup`) |
| Ladeanzeigen („Bitte warten“, WLAN-Suche, Verbinden) über beide Screens | ES-Patch (`GuiLoading` startet standardmäßig oben) |
| BIOS-Prüfung („Fehlende BIOS-Dateien“) über beide Screens verteilt | ES-Patch (`GuiBios`) |
| Spieloptionen als schmale Seitenleiste über die volle Höhe an der Bildschirmgrenze | ES-Patch (`GuiGameOptions`: zentriertes Menü oben wie die übrigen Menüs) |
| „Metadaten dieses Spiels bearbeiten“ über beide Screens verteilt | ES-Patch (`GuiMetaDataEd`) |
| „Spielemedien ansehen“ zog Bilder und Videos über beide Screens | ES-Patch (`GuiImageViewer`: nur oberer Screen) |
| Position von Hauptmenü, Einstellungen, Save State Manager, Tastatur und Bezel Project | ES-Patch (frühere Dual-Screen-Arbeit) |
| Original-ES zeigt beide Theme-Hälften gequetscht auf dem oberen Screen | Ports-Umschalter setzt für das Original-ES ein Einzelbildschirm-Theme |

## Aufbau

```
patches/                     ES-Patch für das ROCKNIX-Buildsystem
installer/                   Installer und Deinstallation (Ports-Einträge)
tools/make-installer.py      baut die Installations-ZIP
device/rgds-test/            Skripte für /storage/rgds-test/ auf dem Gerät
  start-es-dualstation.sh    Startskript der Dual-Version
  rgds-sway-fix.sh           passt die Sway-Config vor jedem Start an
  es-switch-helper.sh        Umschalten single/dual (Theme, Dienst, Sway)
device/ports/                Einträge für /storage/roms/ports/
device/system.d/             Drop-in für essway.service
theme/dii-ess-aye-rgds-plus/ RG-DS-Plus-Variante des Themes dii-ess-aye (MIT)
theme/canvas-ds-rgds-plus-overlay/ Layout-Overlay für canvas-ds (CC BY-NC-SA)
docs/BUILD.de.md             Bauen des ES-Pakets
docs/screenshots/            Screenshots für diese README
docs/zwischenstand-*.md      technische Analyse und Projektstand
```

## Manuelle Installation (für Fortgeschrittene)


Quellcode und **`emulationstation-rgds`** aus dem
[aktuellen Release](https://github.com/Ninte86hl/RetroDualStation/releases/latest)
herunterladen, dann aus dem Quellcode-Ordner:

```bash
ssh root@<IP> mkdir -p /storage/rgds-test
```
```bash
scp emulationstation-rgds device/rgds-test/*.sh installer/payload/uninstall.sh root@<IP>:/storage/rgds-test/
```
```bash
scp device/ports/*.sh installer/payload/ports/*.sh root@<IP>:/storage/roms/ports/
```
```bash
scp -r theme/dii-ess-aye-rgds-plus root@<IP>:/storage/.config/emulationstation/themes/
```

Auf dem Gerät:

```bash
chmod +x /storage/rgds-test/* /storage/roms/ports/*.sh
```
```bash
/storage/rgds-test/es-switch-helper.sh dual
```

Selbst bauen ist optional (siehe [`docs/BUILD.de.md`](BUILD.de.md)); eine
selbst gebaute Datei muss ebenfalls mit `emulationstation-rgds` beginnen.

## Wie es funktioniert

### Sway

ROCKNIX schreibt `/storage/.config/sway/config` bei jedem Boot neu
(`/usr/lib/autostart/common/111-sway-init`). Die Original-Regeln laden bei
jedem neuen ES-Fenster die Config neu und schalten dabei den unteren Screen
aus. Sway-Kriterien sind unverankerte reguläre Ausdrücke,
`[app_id="emulationstation"]` trifft also auch diese Version.

`rgds-sway-fix.sh` ergänzt deshalb vor jedem Start:

```text
for_window [app_id="^emulationstation-rgds"] fullscreen enable global
exec_always swaymsg '[app_id="emulationstation"]' focus output DSI-2, output DSI-1 power on
```

### EmulationStation

Bei 2048 × 768 werden Menüs auf 1024 Pixel Breite zentriert und liegen
damit auf dem oberen Screen:

```cpp
#define RGDS_MENU_W ((Renderer::getScreenWidth() == 2048 && Renderer::getScreenHeight() == 768) ? 1024.0f : (float)Renderer::getScreenWidth())
```

Ladeanzeigen (`GuiLoading`) erscheinen standardmäßig auf dem oberen Screen;
The Bezel Project legt seine Ladeanzeige mit `setLoadingArea()` nach unten.

### Umschalten

Port-Skripte laufen innerhalb von `essway`. Ein direkter Neustart des
Dienstes würde sie mit beenden. Sie starten deshalb `es-switch-helper.sh`
über `systemd-run`. Das Hilfsskript stoppt ES, setzt `ThemeSet` in
`es_settings.cfg`, setzt oder entfernt den Drop-in und startet ES neu.
Protokoll: `/storage/rgds-test/es-switch.log`.
