# RetroDualStation – technical details

🇩🇪 [Deutsch](TECHNIK.md) · [← README](../README.md)

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

## Repository layout

```
patches/                     ES patch for the ROCKNIX build system
installer/                   installer and uninstaller (Ports entries)
tools/make-installer.py      builds the installer ZIP
device/rgds-test/            scripts for /storage/rgds-test/ on the device
  start-es-dualstation.sh    start script of the dual-screen build
  rgds-sway-fix.sh           adjusts the Sway config before every start
  es-switch-helper.sh        switches single/dual (theme, service, Sway)
device/ports/                entries for /storage/roms/ports/
device/system.d/             drop-in for essway.service
theme/dii-ess-aye-rgds-plus/ RG DS Plus variant of the dii-ess-aye theme (MIT)
theme/canvas-ds-rgds-plus-overlay/ layout overlay for canvas-ds (CC BY-NC-SA)
docs/BUILD.md                building the ES package
docs/screenshots/            screenshots used in this README
docs/zwischenstand-*.md      technical analysis and project log (German)
```

## Manual installation (advanced)


Download the source code and **`emulationstation-rgds`** from the
[latest release](https://github.com/Ninte86hl/RetroDualStation/releases/latest),
then from the source folder:

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

On the device:

```bash
chmod +x /storage/rgds-test/* /storage/roms/ports/*.sh
```
```bash
/storage/rgds-test/es-switch-helper.sh dual
```

Building ES yourself is optional (see [`docs/BUILD.md`](BUILD.md)); a
self-built binary must also be named starting with `emulationstation-rgds`.

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
