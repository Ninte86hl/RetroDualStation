# Zwischenstand – RGDS Plus Dual-Screen / EmulationStation

**Stand:** 16. Oktober 2026
**Vorgänger:** Zwischenstand vom 15. Oktober 2026 (dieser hier ersetzt ihn)
**Zweck:** In einem neuen Chat hochladen, um ohne Rekonstruktion weiterzuarbeiten.

---

## 1. Kurzfassung

Die Dual-Screen-Version von EmulationStation (**v5**) läuft stabil und übersteht Neustarts:

- Hauptansicht: oben ROCKNIX-Logo, unten Systemansicht. Die Navigation zwischen den Systemen funktioniert einwandfrei.
- Die Rückkehr aus RetroArch funktioniert, beide Screens bleiben korrekt.
- Scraper, Updates, Downloads, Themes und Info-Meldungen erscheinen vollständig auf dem oberen Screen.
- Save State Manager, Advanced Game Settings, Tastatur und The Bezel Project funktionieren unverändert.
- DS-Spiele über dsperate (eigenständiger Emulator) laufen problemlos.
- Über Ports kann zwischen Dual-ES (v5) und dem Original-ROCKNIX-ES umgeschaltet werden, inklusive Theme-Wechsel.

**Wichtigste Erkenntnis:** Die Fehler bei Navigation und RetroArch-Rückkehr lagen **nicht im ES-Code**, sondern in der Sway-Konfiguration. Der Renderer (`screenWidth`) wurde nicht angefasst und muss es auch nicht.

---

## 2. Umgebung

| Was | Wert |
|---|---|
| Host | Bazzite Linux |
| Arbeitsverzeichnis | `~/rgds-es-build` |
| ES-Quellcode | `~/rgds-es-build/emulationstation-next` (Commit `cada856d86e3115fbbf0bce09dd761b0ee8fa9fd`) |
| ROCKNIX-Buildsystem | `~/rgds-es-build/distribution` |
| Zielgerät | RG DS Plus / RK3566, SSH `root@<GERAETE-IP>` |
| Sway-Socket | `/run/0-runtime-dir/sway-ipc.0.sock` (vor `swaymsg` als `SWAYSOCK` exportieren) |
| Ausgänge | `DSI-2` oben bei 0,0 · `DSI-1` unten bei 1024,0 · je 1024 × 768 |
| ES-Fenster | 2048 × 768, globales Vollbild (`fullscreen_mode` 2) |
| Themes | Dual: `dii-ess-aye-rgds-plus` · Single: `system-theme` (→ `/usr/share/themes/es-theme-art-book-next`) |

Die Uhr des Geräts zeigt EDT. Die Zeitstempel in den Logs liegen deshalb 6 Stunden hinter der lokalen Zeit (Paris).

---

## 3. Gelöst: Sway-Konfiguration (Navigation, RetroArch-Rückkehr)

### Ursache

1. **Sway-Kriterien sind unverankerte reguläre Ausdrücke.** `[app_id="emulationstation"]` passt auch auf `emulationstation-rgds-v5`. Alle ES-Regeln der Original-Config greifen deshalb auch für die Testversion.
2. Nach jedem Spiel baut ES sein Fenster neu auf. Für Sway ist das ein neues Fenster, und folgende Regeln feuern:
   - `for_window [app_id="emulationstation"] move output DP-1` (DP-1 existiert nicht, die Regel ist wirkungslos)
   - `for_window [app_id="emulationstation"] reload` → **Config-Reload** → alle `exec_always`-Zeilen laufen erneut, darunter
   - `exec_always swaymsg '[app_id="emulationstation"]' focus output DSI-2, output DSI-1 power off` → **unterer Screen aus**
3. Das neue Fenster wurde **gekachelt** auf dem fokussierten Workspace abgelegt, mit 1024 × 768. Ein globales Vollbild gab es nicht mehr. Daher stammten „alles auf einem Screen“ und die kaputte Navigation.
4. Ein schwebendes Fenster mit 2048 × 768 bei 0,0 hat seinen Mittelpunkt genau bei x=1024. Sway ordnet es deshalb `DSI-1` bzw. Workspace 2 zu. Das erklärt die früheren, gescheiterten Verschiebe-Versuche.

### Lösung

Zwei Änderungen in `/storage/.config/sway/config`:

```text
for_window [app_id="^emulationstation-rgds"] fullscreen enable global      # neu, nach der DP-1-Regel
exec_always swaymsg '[app_id="emulationstation"]' focus output DSI-2, output DSI-1 power on   # war: power off
```

### Persistenz

`/usr/lib/autostart/common/111-sway-init` **schreibt die Sway-Config bei jedem Boot neu** (`cp` der Vorlage plus angehängte gerätespezifische Zeilen, für das RG DS Plus die Zeilen 210–215). Es gibt kein `include`, und das Skript liegt im schreibgeschützten `/usr`.

→ Deshalb setzt **`/storage/rgds-test/rgds-sway-fix.sh`** die beiden Änderungen vor jedem Start der Testversion erneut (idempotent) und führt `swaymsg reload` aus. Es wird aus `start-es-v2-diag.sh` vor dem `exec` aufgerufen.

---

## 4. Gelöst: Menüs über beide Screens (ES-Code, v3–v5)

### Muster

Wie bei den bereits funktionierenden Dateien (z. B. `GuiBackupStart.cpp`): Bei 2048 × 768 wird auf **1024** statt auf die volle Breite gerechnet. Das legt das Menü auf den oberen Screen (x 0–1023). Umgesetzt als Makro in Zeile 1 der jeweiligen Datei:

```cpp
#define RGDS_MENU_W ((Renderer::getScreenWidth() == 2048 && Renderer::getScreenHeight() == 768) ? 1024.0f : (float)Renderer::getScreenWidth())
```

### Geänderte Dateien

| Datei | Änderung |
|---|---|
| `es-app/src/guis/GuiScraperStart.cpp` | Menüposition (beide Zweige) mit `RGDS_MENU_W`; `GuiLoading` („PLEASE WAIT“) mit `setLoadingArea(0, 0, 1024, 768)` |
| `es-app/src/guis/GuiUpdate.cpp` | `setSize` mit `RGDS_MENU_W` |
| `es-app/src/guis/GuiBatoceraStore.cpp` | `centerWindow()`: `setSize` und `setPosition` mit `RGDS_MENU_W` |
| `es-app/src/guis/GuiThemeInstaller.cpp` | `centerWindow()`: `setSize` und `setPosition` mit `RGDS_MENU_W` |
| `es-app/src/guis/GuiAutoScrape.cpp` | `setSize` mit `RGDS_MENU_W` |
| `es-core/src/guis/GuiInfoPopup.cpp` | `maxWidth`, `paddingX`, `posX` mit `RGDS_MENU_W` (betrifft **alle** Info-Meldungen, z. B. „Scraping finished“) |

`setLoadingArea()` stammt aus dem bestehenden Patch (`GuiLoading.h`). Das Bezel Project nutzt es mit `(1024, 0, 1024, 768)` für den unteren Screen.

### Bewusst nicht geändert

- `es-core/src/components/AsyncNotificationComponent.cpp` (Fortschrittsanzeige): sitzt rechtsbündig unten rechts (`posX = 2048 × 0,99 − Breite`), komplett auf einem Screen. Falls sie nach oben soll: eine Ersetzung in Zeile 62.
- `Renderer.cpp` / `screenWidth`: keine globalen Änderungen. Das Diagnose-Logging (`RGDS SIZE CHANGE`) ist im Patch enthalten und harmlos.

---

## 5. Build-Ablauf (verifiziert)

Das Paket lädt **nicht** den lokalen Quellordner, sondern das GitHub-Archiv von Commit `cada856…`. Lokale Änderungen kommen über **einen** Patch hinein:

`distribution/projects/ROCKNIX/packages/ui/emulationstation/patches/aarch64/001-rgds-menu-dualscreen-v2.patch`

**Immer diese eine Datei überschreiben.** Keine zweite Patch-Datei und keine Sicherung in diesen Ordner legen, sonst wird doppelt gepatcht.

```bash
cd ~/rgds-es-build/emulationstation-next
git diff > ~/rgds-es-build/distribution/projects/ROCKNIX/packages/ui/emulationstation/patches/aarch64/001-rgds-menu-dualscreen-v2.patch
cd ~/rgds-es-build/distribution
PROJECT=ROCKNIX DEVICE=RK3566 ARCH=aarch64 PACKAGE=emulationstation make docker-package 2>&1 | tee ~/rgds-es-build/rgds-vN-build.log
grep -n "Hunk\|FAILED\| error:" ~/rgds-es-build/rgds-vN-build.log | head    # erwartet: keine Ausgabe
```

- Der Build läuft im Podman-Container `ghcr.io/rocknix/rocknix-build:latest`. `.env` wird automatisch erzeugt.
- Die `LC_CTYPE`-/Locale-Zeilen am Ende des Logs sind harmlos.
- Binärdatei: `distribution/build.ROCKNIX-RK3566.aarch64/install_pkg/emulationstation-cada856d86e3115fbbf0bce09dd761b0ee8fa9fd/usr/bin/emulationstation`
- Unter neuem Namen kopieren (`emulationstation-rgds-vN`), per `scp` nach `/storage/rgds-test/`, `chmod +x`, im Startskript per `sed` die Versionsnummer tauschen, `systemctl restart essway`.
- Der Name muss mit `emulationstation-rgds` beginnen, damit die Sway-Vollbild-Regel greift.

**Unversioniert, nicht im Patch:** `es-core/src/renderers/Renderer.cpp.rgds-backup` (alt, **nicht** zurückkopieren).

---

## 6. Dateien auf dem Gerät

| Pfad | Zweck |
|---|---|
| `/storage/rgds-test/emulationstation-rgds-v5` | aktuelle Version (v2-diag, v3, v4 liegen daneben) |
| `/storage/rgds-test/start-es-v2-diag.sh` | Startskript: `es_settings`, Wayland-Variablen, Aufruf `rgds-sway-fix.sh`, `exec … v5 --windowed --resolution 2048 768` |
| `/storage/rgds-test/rgds-sway-fix.sh` | passt die Sway-Config vor jedem Start an und lädt Sway neu |
| `/storage/rgds-test/es-switch-helper.sh` | Umschalten `single`/`dual`: stoppt ES, setzt Theme (`ThemeSet`), Drop-in, Sway-Zeile, startet ES |
| `/storage/roms/ports/RGDS Dual-Screen ES.sh` | Port: `systemd-run --no-block …/es-switch-helper.sh dual` |
| `/storage/roms/ports/RGDS Single-Screen ES.sh` | Port: `systemd-run --no-block …/es-switch-helper.sh single` |
| `/storage/.config/system.d/essway.service.d/rgds.conf` | Drop-in: `ExecStart=` leer, dann `ExecStart=/storage/rgds-test/start-es-v2-diag.sh` (nur im Dual-Modus vorhanden) |
| `/storage/rgds-test/es-switch.log` | Log der Umschaltvorgänge |
| `/storage/rgds-test/es_settings.last-switch.cfg` | Sicherung der ES-Einstellungen vor dem letzten Umschalten |

**Sicherungen:** `start-es-v2-diag.sh.bak-v2`, `start-es-v2-diag.sh.bak-v5`, `/storage/.config/sway/config.bak-2026-10-15` (vor dem Boot-Neuschreiben, nur als Referenz).

**Warum `systemd-run`:** Ports werden von ES gestartet und laufen im `essway`-cgroup. Ein direktes `systemctl restart essway` würde das Skript mit beenden. Das Hilfsskript läuft deshalb außerhalb davon und kann ES sicher stoppen. Das ist auch nötig, damit ES beim Beenden die geänderte `es_settings.cfg` nicht überschreibt.

**Modus nach Geräteneustart:** Es bleibt der zuletzt gewählte Modus (Drop-in vorhanden = Dual).

## 7. Dateien auf dem Host (`~/rgds-es-build`)

- `stand-2026-10-15.patch`, `stand-vor-menuepatch.patch` – Sicherungen des Arbeitsstands
- `001-alt-2026-10-15.patch` – alter Patch vor den Menü-Änderungen
- `emulationstation-rgds-v3`, `-v4`, `-v5` – gebaute Binärdateien
- `rgds-v3-build.log`, `rgds-v4-build.log`, `rgds-v5-build.log`
- `rgds-sway-fix.sh`, `es-switch-helper.sh`, die beiden Port-Skripte

---

## 8. Weitere Befunde

- **Logging:** ES schreibt standardmäßig nur `WARNING` und höher. `LogInfo`-Diagnosen (`RGDS SIZE CHANGE`, `RGDS-V2 SDL RESIZE`) erscheinen **nicht** in `/var/log/es_log.txt`. Für künftige Diagnosen `LogWarning` verwenden oder die Log-Stufe erhöhen.
- **ScreenScraper und RetroAchievements fehlen in der eigenen Version:** `Scraper.cpp` meldet ScreenScraper nur mit `#ifdef SCREENSCRAPER_DEV_LOGIN` an. `package.mk` liest `SCREENSCRAPER_DEV_LOGIN` und `CHEEVOS_DEV_LOGIN` aus Umgebungsvariablen, die nur der offizielle Build hat. → **Zum Scrapen per Port auf Single wechseln** (Original-ES), danach zurück auf Dual. Medien und Gamelists werden geteilt.
- **ArcadeDB:** Unterstützt nur Arcade-Systeme, die Liste ohne Arcade-Spiele ist korrekt leer. Nach dem Umweg über IGDB bleibt die Systemliste beim Zurückschalten stehen (ES-Eigenheit, nicht durch den Patch verursacht). Für NES/SNES/GB IGDB oder ScreenScraper (Single) nutzen.
- **`vertical-check`** (`/usr/bin/vertical-check`) reagiert nur auf Fenster mit Titel `RetroArch…`. Für vertikale Spiele (melonDS/DeSmuME/bestimmte Arcade-ROMs) stapelt es beim RG DS Plus die Screens (`DSI-1` auf 0,768, RetroArch-Fenster 1024 × 1536) und setzt das danach **nicht** zurück. Bei nicht-vertikalen Spielen startet es `lowerdeck` auf `DSI-1`.

---

## 9. Offene Punkte

1. **Schwarzer Bildschirm beim Scrape-Start** (beide Screens, danach automatische Rückkehr in die Systemansicht): einmal mit v4 aufgetreten, danach nicht mehr reproduzierbar. Bei erneutem Auftreten zuerst den Screenshot-Test (`which grim`, dann `sleep 3; grim /storage/rgds-test/scrape-black.png` und sofort den Scrape starten), danach der Vergleich mit der v2-diag.
2. **RetroArch-DS-Cores ungetestet:** Mit melonDS/DeSmuME über RetroArch würde `vertical-check` die Screens stapeln. Ob der Config-Reload bei der Rückkehr das wieder richtet, ist offen. Nur relevant, wenn DS-Spiele über RetroArch laufen sollen (derzeit dsperate).
3. Optional: Fortschrittsanzeige des Scrapers nach oben verlegen (`AsyncNotificationComponent.cpp` Zeile 62).
4. Weitere Menüs und Dialoge bei Bedarf nach demselben `RGDS_MENU_W`-Muster prüfen. Kandidaten finden mit `grep -rln "2048" es-app/src es-core/src` im Abgleich mit den Klassennamen.

---

## 10. Arbeitsregeln

- Kommunikation und Anweisungen auf Deutsch.
- Keine Bilder erstellen; Screenshots sind nur Diagnosematerial.
- Kurze, einzelne Befehle statt langer mehrzeiliger Blöcke (ein früherer mehrzeiliger Befehl hat das Terminal geschlossen).
- Vor Änderungen den Dateiinhalt und `git diff` prüfen. `sed` mit Zeilennummern nur nach vorheriger Kontrolle der Zeile; erst ersetzen, dann Zeilen einfügen.
- Keine alten Sicherungen blind zurückkopieren.
- Keine globalen Änderungen an `Renderer::getScreenWidth()`/`screenWidth`.
- Die funktionierenden Ansichten erhalten: Save State Manager, Advanced Game Settings, Tastatur, The Bezel Project, Menüs oben, Hauptnavigation.
- Host-Befehle im Ordner `~/rgds-es-build/emulationstation-next` ausführen (Build-Befehle in `distribution`). Geräte-Befehle per SSH.
