# Build (Deutsch)

🇬🇧 [English version](BUILD.md)

Gebaut wird nur das Paket `emulationstation` im ROCKNIX-Buildsystem, kein
vollständiges System-Image.

## Voraussetzungen

- Linux-Host mit Podman oder Docker
- [ROCKNIX/distribution](https://github.com/ROCKNIX/distribution) ausgecheckt
- Der Paketordner `projects/ROCKNIX/packages/ui/emulationstation/` zeigt in
  `package.mk` auf Commit `cada856d86e3115fbbf0bce09dd761b0ee8fa9fd`
  (`PKG_VERSION`). Bei einer anderen Version muss der Patch eventuell
  angepasst werden.

## Ablauf

```bash
cp patches/001-rgds-menu-dualscreen.patch patches/002-rds-gameswitcher-chain.patch patches/003-rds-bluetooth-systemcfg-navbar.patch patches/004-rds-screens.patch patches/005-rds-theme-screen-vars.patch patches/006-rds-no-es-volume-popup.patch \
   /pfad/zu/distribution/projects/ROCKNIX/packages/ui/emulationstation/patches/aarch64/
```

```bash
cd /pfad/zu/distribution
```

```bash
PROJECT=ROCKNIX DEVICE=RK3566 ARCH=aarch64 PACKAGE=emulationstation make docker-package 2>&1 | tee build.log
```

Danach prüfen, ob der Patch sauber angewendet wurde und nichts fehlgeschlagen ist:

```bash
grep -n "Hunk\|FAILED\| error:" build.log | head
```

Erwartet wird: keine Ausgabe. Die vielen `LC_CTYPE`-/Locale-Zeilen am Ende
des Logs stammen aus dem Glibc-Locale-Build und sind harmlos.

Im Ordner `patches/aarch64/` dürfen nur unsere Patches (`001-…`, `002-…`, `003-…`, `004-…`, `005-…`, `006-…`) liegen. Bis v8
hieß der Patch `001-rgds-menu-dualscreen-v2.patch` – diese alte Datei
vorher löschen, sonst wird sie zusätzlich angewendet und der Build schlägt fehl.

## Ergebnis

```
build.ROCKNIX-RK3566.aarch64/install_pkg/emulationstation-<commit>/usr/bin/emulationstation
```

Die Datei unter einem Namen kopieren, der mit `emulationstation-rgds`
beginnt (der Installer nutzt `emulationstation-rgds`). Sonst greift die Sway-Regel
für das globale Vollbild nicht.

## Hinweis: ScreenScraper und RetroAchievements

`package.mk` liest `SCREENSCRAPER_DEV_LOGIN` und `CHEEVOS_DEV_LOGIN` aus
Umgebungsvariablen. Die offiziellen Werte sind nicht öffentlich. Ein
eigener Build enthält ScreenScraper deshalb nicht (`#ifdef` in
`Scraper.cpp`), und RetroAchievements fehlen ebenfalls. Zum Scrapen mit
ScreenScraper per Port auf das Original-ES umschalten (siehe README).
