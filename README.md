# dii-ess-aye-rocknix-dual mod

🇩🇪 [Deutsche Anleitung](README.de.md)

Dual-screen EmulationStation for the **Anbernic RG DS Plus** running
**ROCKNIX** (RK3566). EmulationStation spans both displays (2048 × 768):
the ROCKNIX logo on the top screen, the system view on the bottom screen.
Menus and notifications stay cleanly on the top screen.

![Main view: ROCKNIX logo on the top screen, system carousel on the bottom screen](docs/screenshots/main.png)

*Left half: top screen · right half: bottom screen (2048 × 768).*

Designed for **dii-ess-aye-rgds-plus**, my RG DS Plus adaptation of
[dii-ess-aye](https://github.com/beebono/dii-ess-aye) by beebono, who made
the original theme for the RG DS.

> **About the theme:** dii-ess-aye is licensed under the MIT License by
> beebono, who kindly allowed the RG DS Plus variant to be shared. The
> variant is included in [`theme/dii-ess-aye-rgds-plus/`](theme/dii-ess-aye-rgds-plus/),
> together with the original license and copyright notice.

---

## What works

- Main view across both screens, navigation between systems
- Returning from RetroArch and other emulators without the bottom screen switching off
- Scraper, updates, downloads, themes and info popups on the top screen
- Save State Manager, Advanced Game Settings, on-screen keyboard, The Bezel Project
- Switching between this build and stock ROCKNIX ES via **Ports**, including a theme switch
- Survives device reboots

## Screenshots

| | |
|---|---|
| ![Game list](docs/screenshots/gamelist.png) | ![Main menu](docs/screenshots/menu.png) |
| **Game list** – preview on top, game carousel and description on the bottom | **Main menu** on the top screen |
| ![Scraper](docs/screenshots/scraper.png) | ![Keyboard](docs/screenshots/keyboard.png) |
| **Scraper** menu on the top screen | **On-screen keyboard** on the bottom screen, settings on top |

## Issues fixed for dii-ess-aye on the RG DS Plus

These problems are not bugs in the theme itself. They come from how stock
ES and ROCKNIX's Sway rules handle a 2048 × 768 window. This mod fixes them
in EmulationStation and the Sway setup, so the theme can work as intended:

| Problem with stock ES / ROCKNIX | Fixed by |
|---|---|
| Bottom screen switched off and everything moved to the top screen after returning from a game | Sway rules (`rgds-sway-fix.sh`) |
| Navigation between systems in the main view stopped working | Sway: global fullscreen across both outputs |
| ES window shrank to one screen (1024 × 768) after a game or a restart | Sway: global fullscreen across both outputs |
| Fixes were lost after every reboot (ROCKNIX rewrites the Sway config) | `rgds-sway-fix.sh` runs before every start |
| Scraper, updates, downloads and theme menus drawn across both screens | ES patch (`RGDS_MENU_W`) |
| Info popups (e.g. "Scraping finished") split across both screens | ES patch (`GuiInfoPopup`) |
| Loading screens ("Please wait", Wi-Fi search, connecting) spanning both screens | ES patch (`GuiLoading` defaults to the top screen) |
| "Missing BIOS files" check spread across both screens | ES patch (`GuiBios`) |
| Game options opened as a narrow full-height side panel at the screen border | ES patch (`GuiGameOptions`: centered menu on the top screen, like the other menus) |
| "Edit this game's metadata" spread across both screens | ES patch (`GuiMetaDataEd`) |
| "View game media" stretched images and videos across both screens | ES patch (`GuiImageViewer`: top screen only) |
| Main menu, settings, Save State Manager, keyboard and Bezel Project placement | ES patch (earlier dual-screen work) |
| Stock ES showing both theme halves squeezed onto the top screen | Ports switch sets a single-screen theme for stock ES |

## Limitations

- **No ScreenScraper and no RetroAchievements** in this build (release or self-built). The
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
theme/dii-ess-aye-rgds-plus/ RG DS Plus variant of the dii-ess-aye theme (MIT)
docs/BUILD.md                building the ES package
docs/screenshots/            screenshots used in this README
docs/zwischenstand-*.md      technical analysis and project log (German)
```

---

## Installation

Download **`dii-ess-aye-rocknix-dual-mod-v7.tar.gz`** from the
[latest release](https://github.com/Ninte86hl/dii-ess-aye-rocknix-dual-mod/releases/latest)
and unpack it on your computer:

```bash
tar xzf dii-ess-aye-rocknix-dual-mod-v7.tar.gz
```
```bash
cd dii-ess-aye-rocknix-dual-mod-v7
```

The package contains the ready-built ES binary `emulationstation-rgds-v7`.
Building it yourself is optional (see [`docs/BUILD.md`](docs/BUILD.md)); a
self-built binary must also be named starting with `emulationstation-rgds`.

Replace `<IP>` with the IP address of your device.

**1. Create the folders on the device:**
```bash
ssh root@<IP> mkdir -p /storage/rgds-test /storage/.config/system.d/essway.service.d
```

**2. Copy the files (from the unpacked folder):**
```bash
scp emulationstation-rgds-v7 device/rgds-test/*.sh root@<IP>:/storage/rgds-test/
```
```bash
scp device/ports/*.sh root@<IP>:/storage/roms/ports/
```
```bash
scp device/system.d/essway.service.d/rgds.conf root@<IP>:/storage/.config/system.d/essway.service.d/
```
```bash
scp -r theme/dii-ess-aye-rgds-plus root@<IP>:/storage/.config/emulationstation/themes/
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

The switch to **dual** also sets the theme to *dii-ess-aye-rgds-plus*.
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

Loading screens (`GuiLoading`) default to the top screen; The Bezel Project
moves its loading screen to the bottom screen with `setLoadingArea()`.

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
authors. The theme is MIT licensed by beebono (see `CREDITS.md`). Logos and artwork visible
in screenshots belong to their respective owners.
