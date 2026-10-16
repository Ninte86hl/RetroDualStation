# dii-ess-aye-rocknix-dual mod

🇩🇪 [Deutsche Anleitung](README.de.md)

Dual-screen EmulationStation for the **Anbernic RG DS Plus** running
**ROCKNIX** (RK3566). EmulationStation spans both displays (2048 × 768):
the ROCKNIX logo on the top screen, the system view on the bottom screen.
Menus and notifications stay cleanly on the top screen.

Designed for the **dii-ess-aye-rgds-plus** theme, based on [dii-ess-aye](https://github.com/beebono/dii-ess-aye) by beebono (not included, get it from the original project).

---

## What works

- Main view across both screens, navigation between systems
- Returning from RetroArch and other emulators without the bottom screen switching off
- Scraper, updates, downloads, themes and info popups on the top screen
- Save State Manager, Advanced Game Settings, on-screen keyboard, The Bezel Project
- Switching between this build and stock ROCKNIX ES via **Ports**, including a theme switch
- Survives device reboots

## Limitations

- **No ScreenScraper and no RetroAchievements** in a self-built ES. The
  required developer credentials are only available to the official
  ROCKNIX build. To scrape with ScreenScraper, switch to **Single** via
  Ports, then back to **Dual**. Media and gamelists are shared.
- DS games through RetroArch cores (melonDS/DeSmuME) are untested.
  Standalone emulators such as DraStic or dsperate work.
- Tested on ROCKNIX with EmulationStation commit `cada856d86e3`.

---

## Repository layout

```
patches/                     ES patch for the ROCKNIX build system
device/rgds-test/            scripts for /storage/rgds-test/ on the device
  start-es-v2-diag.sh        start script of the dual-screen build
  rgds-sway-fix.sh           adjusts the Sway config before every start
  es-switch-helper.sh        switches single/dual (theme, service, Sway)
device/ports/                entries for /storage/roms/ports/
device/system.d/             drop-in for essway.service
docs/BUILD.md                building the ES package
docs/zwischenstand-*.md      technical analysis and project log (German)
```

---

## Installation

Requirement: a built ES binary (see [`docs/BUILD.md`](docs/BUILD.md)) named
`emulationstation-rgds-v5`. The name must start with `emulationstation-rgds`.

Replace `<IP>` with the IP address of your device.

**1. Create the folders on the device:**
```bash
ssh root@<IP> mkdir -p /storage/rgds-test /storage/.config/system.d/essway.service.d
```

**2. Copy the files (from the repository folder):**
```bash
scp emulationstation-rgds-v5 device/rgds-test/*.sh root@<IP>:/storage/rgds-test/
```
```bash
scp device/ports/*.sh root@<IP>:/storage/roms/ports/
```
```bash
scp device/system.d/essway.service.d/rgds.conf root@<IP>:/storage/.config/system.d/essway.service.d/
```

**3. On the device, make them executable and activate:**
```bash
chmod +x /storage/rgds-test/* /storage/roms/ports/RGDS*.sh
```
```bash
systemctl daemon-reload
```
```bash
/storage/rgds-test/es-switch-helper.sh dual
```

Afterwards use the **Ports** entries *RGDS Dual-Screen ES* and
*RGDS Single-Screen ES*. If they don't show up, update the gamelists.

## Uninstall

Switch to **Single** via Ports. This removes the drop-in and restores stock
ES. Then `/storage/rgds-test/` and the two port scripts can be deleted.

---

## How it works

### Sway

ROCKNIX rewrites `/storage/.config/sway/config` on every boot
(`/usr/lib/autostart/common/111-sway-init`). The stock rules reload the
config for every new ES window and switch off the bottom screen in the
process. Sway criteria are unanchored regular expressions, so
`[app_id="emulationstation"]` also matches this build.

`rgds-sway-fix.sh` therefore adds before every start:

```text
for_window [app_id="^emulationstation-rgds"] fullscreen enable global
exec_always swaymsg '[app_id="emulationstation"]' focus output DSI-2, output DSI-1 power on
```

### EmulationStation

At 2048 × 768, menus are centered within a width of 1024 pixels, which
places them on the top screen:

```cpp
#define RGDS_MENU_W ((Renderer::getScreenWidth() == 2048 && Renderer::getScreenHeight() == 768) ? 1024.0f : (float)Renderer::getScreenWidth())
```

Loading screens are limited to one screen with `setLoadingArea()`.

### Switching

Port scripts run inside `essway`. Restarting the service directly would
kill them as well, so they launch `es-switch-helper.sh` through
`systemd-run`. The helper stops ES, sets `ThemeSet` in `es_settings.cfg`,
adds or removes the drop-in and starts ES again.
Log: `/storage/rgds-test/es-switch.log`.

---

## Credits

Built on the work of the ROCKNIX and Batocera teams, the original
EmulationStation, and beebono's dii-ess-aye theme. See
[`CREDITS.md`](CREDITS.md) for the full list. Thank you! 🙏

## License

Scripts and documentation: MIT (see [`LICENSE`](LICENSE)).
The patch modifies [ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next),
which is also MIT licensed; its copyright notices remain with the original
authors. The theme is not part of this repository. Logos and artwork visible
in screenshots belong to their respective owners.
