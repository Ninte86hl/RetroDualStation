# dii-ess-aye-rocknix-dual mod – Anleitung (Deutsch)

🇬🇧 [English version](README.md)

Dual-Screen-EmulationStation für das **Anbernic RG DS Plus** unter
**ROCKNIX** (RK3566). EmulationStation läuft über beide Bildschirme
(2048 × 768): oben das ROCKNIX-Logo, unten die Systemansicht. Menüs und
Meldungen erscheinen sauber auf dem oberen Screen.

Gedacht für das Theme **dii-ess-aye-rgds-plus**.

---

## Was funktioniert

- Hauptansicht über beide Screens, Navigation zwischen den Systemen
- Rückkehr aus RetroArch und anderen Emulatoren, ohne dass der untere Screen ausgeht
- Scraper, Updates, Downloads, Themes und Info-Meldungen auf dem oberen Screen
- Save State Manager, Advanced Game Settings, Bildschirmtastatur, The Bezel Project
- Umschalten zwischen dieser Version und dem Original-ES über **Ports**, inklusive Theme-Wechsel
- Übersteht Neustarts des Geräts

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

## Lizenz

Skripte und Dokumentation: MIT (siehe [`LICENSE`](LICENSE)).
Der Patch ändert [ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next),
das unter seiner eigenen Lizenz steht.
