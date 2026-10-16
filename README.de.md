# dii-ess-aye-rocknix-dual mod – Anleitung (Deutsch)

🇬🇧 [English version](README.md)

Dual-Screen-EmulationStation für das **Anbernic RG DS Plus** unter
**ROCKNIX** (RK3566). EmulationStation läuft über beide Bildschirme
(2048 × 768): oben das ROCKNIX-Logo, unten die Systemansicht. Menüs und
Meldungen erscheinen sauber auf dem oberen Screen.

Gedacht für **dii-ess-aye-rgds-plus**, meine Anpassung von
[dii-ess-aye](https://github.com/beebono/dii-ess-aye) für das RG DS Plus.
Das Original-Theme für das RG DS stammt von beebono.

> **Zum Theme:** Das Theme ist **nicht enthalten**. Das Original hat
> bisher keine Lizenz. Da die RG-DS-Plus-Variante darauf aufbaut, wurde die
> Erlaubnis zu ihrer Weitergabe bei beebono angefragt; eine Antwort steht
> noch aus. Bitte das Theme vom
> [Originalprojekt](https://github.com/beebono/dii-ess-aye) beziehen.

---

## Was funktioniert

- Hauptansicht über beide Screens, Navigation zwischen den Systemen
- Rückkehr aus RetroArch und anderen Emulatoren, ohne dass der untere Screen ausgeht
- Scraper, Updates, Downloads, Themes und Info-Meldungen auf dem oberen Screen
- Save State Manager, Advanced Game Settings, Bildschirmtastatur, The Bezel Project
- Umschalten zwischen dieser Version und dem Original-ES über **Ports**, inklusive Theme-Wechsel
- Übersteht Neustarts des Geräts

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
| Ladeanzeigen („Bitte warten“) über beide Screens | ES-Patch (`setLoadingArea`) |
| Position von Hauptmenü, Einstellungen, Save State Manager, Tastatur und Bezel Project | ES-Patch (frühere Dual-Screen-Arbeit) |
| Original-ES zeigt beide Theme-Hälften gequetscht auf dem oberen Screen | Ports-Umschalter setzt für das Original-ES ein Einzelbildschirm-Theme |

## Einschränkungen

- **Kein ScreenScraper und keine RetroAchievements** in der selbst gebauten
  Version. Die nötigen Entwicklerzugangsdaten bekommt nur der offizielle
  ROCKNIX-Build. Zum Scrapen per Port auf **Single** wechseln, danach
  zurück auf **Dual**. Medien und Gamelists werden geteilt.
- DS-Spiele über RetroArch-Cores (melonDS/DeSmuME) sind ungetestet.
  Eigenständige Emulatoren wie DraStic oder dsperate funktionieren.
- Getestet auf ROCKNIX mit EmulationStation-Commit `cada856d86e3`.

---

## Aufbau

```
patches/                     ES-Patch für das ROCKNIX-Buildsystem
device/rgds-test/            Skripte für /storage/rgds-test/ auf dem Gerät
  start-es-v2-diag.sh        Startskript der Dual-Version
  rgds-sway-fix.sh           passt die Sway-Config vor jedem Start an
  es-switch-helper.sh        Umschalten single/dual (Theme, Dienst, Sway)
device/ports/                Einträge für /storage/roms/ports/
device/system.d/             Drop-in für essway.service
docs/BUILD.de.md                Bauen des ES-Pakets
docs/zwischenstand-*.md      technische Analyse und Projektstand
```

---

## Installation

Voraussetzung: eine gebaute ES-Binärdatei (siehe [`docs/BUILD.de.md`](docs/BUILD.de.md)),
benannt als `emulationstation-rgds-v5`. Der Name muss mit
`emulationstation-rgds` beginnen.

`<IP>` durch die IP-Adresse des Geräts ersetzen.

**1. Ordner auf dem Gerät anlegen:**
```bash
ssh root@<IP> mkdir -p /storage/rgds-test /storage/.config/system.d/essway.service.d
```

**2. Dateien übertragen (vom Repo-Ordner aus):**
```bash
scp emulationstation-rgds-v5 device/rgds-test/*.sh root@<IP>:/storage/rgds-test/
```
```bash
scp device/ports/*.sh root@<IP>:/storage/roms/ports/
```
```bash
scp device/system.d/essway.service.d/rgds.conf root@<IP>:/storage/.config/system.d/essway.service.d/
```

**3. Auf dem Gerät ausführbar machen und aktivieren:**
```bash
chmod +x /storage/rgds-test/* /storage/roms/ports/RGDS*.sh
```
```bash
systemctl daemon-reload
```
```bash
/storage/rgds-test/es-switch-helper.sh dual
```

Danach in ES unter **Ports** die Einträge *RGDS Dual-Screen ES* und
*RGDS Single-Screen ES* nutzen. Falls sie fehlen: Spielelisten aktualisieren.

## Deinstallation

Per Port auf **Single** wechseln. Das entfernt den Drop-in und stellt das
Original-ES wieder her. Danach können `/storage/rgds-test/` und die beiden
Port-Skripte gelöscht werden.

---

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

Ladeanzeigen werden mit `setLoadingArea()` auf einen Screen begrenzt.

### Umschalten

Port-Skripte laufen innerhalb von `essway`. Ein direkter Neustart des
Dienstes würde sie mit beenden. Sie starten deshalb `es-switch-helper.sh`
über `systemd-run`. Das Hilfsskript stoppt ES, setzt `ThemeSet` in
`es_settings.cfg`, setzt oder entfernt den Drop-in und startet ES neu.
Protokoll: `/storage/rgds-test/es-switch.log`.

---

## Danksagung

Dieses Projekt baut auf der Arbeit der ROCKNIX- und Batocera-Teams, dem
ursprünglichen EmulationStation und dem Theme dii-ess-aye von beebono auf.
Die vollständige Liste steht in [`CREDITS.md`](CREDITS.md). Vielen Dank! 🙏

## Lizenz

Skripte und Dokumentation: MIT (siehe [`LICENSE`](LICENSE)).
Der Patch ändert [ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next),
das ebenfalls unter der MIT-Lizenz steht; die Urheberrechtsvermerke bleiben
bei den ursprünglichen Autoren. Das Theme ist nicht Teil dieses Repositorys.
Auf Screenshots sichtbare Logos und Grafiken gehören ihren jeweiligen Eigentümern.
