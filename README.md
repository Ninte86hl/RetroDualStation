# ROCKNIX DualStation

**Dual-screen EmulationStation for ROCKNIX** – Anbernic RG DS Plus (RG DS support is in the works).
*Formerly “dii-ess-aye-rocknix-dual mod”.*

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

**Also supported:** [canvas-ds](https://github.com/toniremi/canvas-ds) by toniremi,
via a small overlay in [`theme/canvas-ds-rgds-plus-overlay/`](theme/canvas-ds-rgds-plus-overlay/)
(shared with his permission, CC BY-NC-SA). The Ports switch remembers which
theme you use in each mode. It has its own installer ZIP in the release
(`canvas-ds-rgds-plus-v9.zip`, unpack into `ports` like the main ZIP).
It comes with five game list views: Gamecarousel, Detailed, Grid, Showcase and Spotlight.

---

## What works

- Main view across both screens, navigation between systems
- Returning from RetroArch and other emulators without the bottom screen switching off
- Scraper, updates, downloads, themes and info popups on the top screen
- Save State Manager, Advanced Game Settings, on-screen keyboard, The Bezel Project
- Switching between this build and stock ROCKNIX ES via **Ports**, including a theme switch
- Survives device reboots
- Left/right in the game list no longer jumps to another system in dual mode (L2/R2 still switch systems); single mode keeps your own setting

## Control Center (preview)

> Work in progress – not part of a release yet.

One button opens a control center on the bottom screen – over ES, RetroArch, DraStic or DSperate.
The running game pauses automatically and continues where you left off.

- Brightness (top/bottom), volume, performance modes
- Wi-Fi and Bluetooth: switch networks, pair controllers – no menu digging
- On-screen keyboard (long-press for ä, é, ñ …), touch and D-pad, external controllers
- Dark/light mode, accent colours, English and German

| | |
|---|---|
| ![Control Center](docs/screenshots/control-center-main.png) | ![Wi-Fi](docs/screenshots/control-center-wifi.png) |
| **Control Center** over a paused game | **Wi-Fi** – saved networks on top |
| ![Bluetooth](docs/screenshots/control-center-bluetooth.png) | ![Keyboard](docs/screenshots/control-center-keyboard.png) |
| **Bluetooth** – pair controllers directly | **On-screen keyboard** for Wi-Fi passwords |

Coming next: save states and shortcuts, RetroAchievements, game switcher, power menu.
Details: [docs/KONTROLLCENTER.md](docs/KONTROLLCENTER.md) (German).

## Screenshots

| | |
|---|---|
| ![Game list](docs/screenshots/gamelist.png) | ![Main menu](docs/screenshots/menu.png) |
| **Game list** – preview on top, game carousel and description on the bottom | **Main menu** on the top screen |
| ![Scraper](docs/screenshots/scraper.png) | ![Keyboard](docs/screenshots/keyboard.png) |
| **Scraper** menu on the top screen | **On-screen keyboard** on the bottom screen, settings on top |
| ![Game options](docs/screenshots/gameoptions.png) | |
| **Game options** on the top screen, game list stays visible below | |

### canvas-ds

![canvas-ds system view](docs/screenshots/canvas-system.png)
**System view** with the [canvas-ds](https://github.com/toniremi/canvas-ds) overlay.

Game list views (top screen: hero image, the video fades in after 5 seconds):

**Automatic / Gamecarousel** – three square icons side by side, the selected one larger, its name below.
![canvas-ds Gamecarousel](docs/screenshots/canvas-view-gamecarousel.png)

**Detailed** – large 2:3 cover with title, description, players, year and developer.
![canvas-ds Detailed](docs/screenshots/canvas-view-detailed.png)

**Grid** – the canvas-ds game grid without the info bars, covers fill the bottom screen.
![canvas-ds Grid](docs/screenshots/canvas-view-grid.png)

**Showcase** – large 2:3 cover on the left, game names as a vertical list on the right.
![canvas-ds Showcase](docs/screenshots/canvas-view-showcase.png)

**Spotlight** – one large card with cover and logo that slides in from the side, like the system view.
![canvas-ds Spotlight](docs/screenshots/canvas-view-spotlight.png)

Artwork names: icon `romname-icon.png`, cover `romname-box.png`, hero `romname-hero.png`, logo `marquee`
from the scraper. The RocknixDS Artwork Manager
creates the first three; missing images fall back to the ScreenScraper media.

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

> **DraStic tip:** If the touchscreen does not respond in DraStic, set
> **Follow 3D Renderer** to *Auto* in the advanced system settings. This
> also happens with stock ROCKNIX ES (Single) and is not caused by this mod.

---

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

---

## Installation

### Easy way: installer via Ports (recommended)

1. Download **`rocknix-dualstation-v9.zip`** from the
   [latest release](https://github.com/Ninte86hl/rocknix-dualstation/releases/latest).
2. Unpack it into the **`ports`** folder of your ROMs
   (`/storage/roms/ports`). It contains `Install ROCKNIX DualStation.sh`
   and a hidden folder `.dualstation`.
3. In EmulationStation, open **Ports** and start
   **Install ROCKNIX DualStation**. If the entry is missing, update the
   game lists first.

The screen goes black for a moment, the bottom screen switches on and ES
comes back across both screens with the *dii-ess-aye-rgds-plus* theme.
Afterwards **Ports** contains *RGDS Dual-Screen ES*, *RGDS Single-Screen ES*
and *Uninstall ROCKNIX DualStation*.

Before changing anything, the installer checks that the device is an
RG DS Plus and that the included EmulationStation works with your ROCKNIX
version. If not, it shows a message in ES and changes nothing.
Log: `/storage/dualstation-install.log`.

**How to get the ZIP into `ports`:** if your ROMs are on a card your
computer can read, copy it there directly. If `/storage/roms` is an ext4
partition (as on many RG DS Plus setups), copy it over the network
(replace `<IP>` with the IP address of your device):

```bash
scp rocknix-dualstation-v9.zip root@<IP>:/storage/roms/ports/
```

Then on the device (SSH):

```bash
cd /storage/roms/ports && unzip rocknix-dualstation-v9.zip && rm rocknix-dualstation-v9.zip
```

Updating from an earlier version works the same way: unpack the new ZIP
and start the installer again.

### Manual installation (advanced)

Download the source code and **`emulationstation-rgds`** from the
[latest release](https://github.com/Ninte86hl/rocknix-dualstation/releases/latest),
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

Building ES yourself is optional (see [`docs/BUILD.md`](docs/BUILD.md)); a
self-built binary must also be named starting with `emulationstation-rgds`.

## Uninstall

Start **Ports → Uninstall ROCKNIX DualStation**. It switches back to stock
ROCKNIX ES and its theme and removes all files of ROCKNIX DualStation
(scripts, theme, Ports entries). Games, media, game lists and saves are not
touched. Log: `/storage/dualstation-uninstall.log`.

Only switching back temporarily (e.g. for scraping)? Use
**RGDS Single-Screen ES** instead and **RGDS Dual-Screen ES** to return.

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
EmulationStation, beebono's dii-ess-aye theme and toniremi's canvas-ds theme. See
[`CREDITS.md`](CREDITS.md) for the full list. Thank you! 🙏

## License

Scripts and documentation: MIT (see [`LICENSE`](LICENSE)).
The patch modifies [ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next),
which is also MIT licensed; its copyright notices remain with the original
authors. The theme is MIT licensed by beebono (see `CREDITS.md`). Logos and artwork visible
in screenshots belong to their respective owners.
