# Build

🇩🇪 [Deutsche Version](BUILD.de.md)

Only the `emulationstation` package is built in the ROCKNIX build system,
not a full system image.

## Requirements

- Linux host with Podman or Docker
- [ROCKNIX/distribution](https://github.com/ROCKNIX/distribution) checked out
- In `projects/ROCKNIX/packages/ui/emulationstation/package.mk`,
  `PKG_VERSION` points to commit `cada856d86e3115fbbf0bce09dd761b0ee8fa9fd`.
  With a different version the patch may need adjusting.

## Steps

```bash
cp patches/001-rgds-menu-dualscreen-v2.patch \
   /path/to/distribution/projects/ROCKNIX/packages/ui/emulationstation/patches/aarch64/
```

```bash
cd /path/to/distribution
```

```bash
PROJECT=ROCKNIX DEVICE=RK3566 ARCH=aarch64 PACKAGE=emulationstation make docker-package 2>&1 | tee build.log
```

Then check that the patch applied cleanly and nothing failed:

```bash
grep -n "Hunk\|FAILED\| error:" build.log | head
```

Expected: no output. The many `LC_CTYPE`/locale lines at the end of the log
come from the glibc locale build and are harmless.

Only **one** patch file may be in the `patches/aarch64/` folder. A second
file would be applied as well and fail.

## Result

```
build.ROCKNIX-RK3566.aarch64/install_pkg/emulationstation-<commit>/usr/bin/emulationstation
```

Copy the file under a name starting with `emulationstation-rgds`
(e.g. `emulationstation-rgds-v6`). Otherwise the Sway rule for global
fullscreen does not apply.

## Note: ScreenScraper and RetroAchievements

`package.mk` reads `SCREENSCRAPER_DEV_LOGIN` and `CHEEVOS_DEV_LOGIN` from
environment variables. The official values are not public, so a self-built
ES does not include ScreenScraper (`#ifdef` in `Scraper.cpp`), and
RetroAchievements are missing too. To scrape with ScreenScraper, switch to
stock ES via Ports (see README).
