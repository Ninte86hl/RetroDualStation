🇩🇪 [Deutsch](Dateien)

# RDS files

What RetroDualStation creates on the device and what it is for. Almost everything starts with **`rds-`**, so it is easy
to spot in a file manager. **Uninstall RDS** removes everything listed here (except the uninstall log and the Artwork
Manager's data) and restores your original settings. Games, artwork, game lists, save states and saves are never touched.

## Program – `/storage/rds-install/`

| File | What for |
|---|---|
| `emulationstation-rgds` | EmulationStation across both screens |
| `start-es-dualstation.sh`, `rgds-sway-fix.sh` | start ES in dual mode and set up Sway for it |
| `es-switch-helper.sh` | switches between dual and single mode (theme, settings, power button) |
| `uninstall.sh` | uninstaller |
| `rds-settings.py` | saves the original values of settings RDS changes and restores them |
| `settings-before-rds.json` | those original values (per setting) |
| `rds-migrate-savestates.py` | one-time move of old save states to slots 1–9 |
| `rgds-diag.sh`, `diag-*.txt` | diagnostics for bug reports |
| `es_settings.before-install.cfg`, `bottomscreen.before` | ES settings / bottom screen from before the first install |
| `theme.single`, `theme.dual`, `subsets.single`, `subsets.dual`, `quicksystemselect.single` | theme and theme options per mode |
| `es-switch.log`, `es_settings.last-switch.cfg` | log and state before the last mode switch |
| `VERSION` | installed version |

(Up to v15.1 the folder was called `rgds-test` – updating renames it.)

## Logs – `/storage/`

| File | What for |
|---|---|
| `rds-install.log` | installation and updates |
| `rds-uninstall.log` | uninstall – deliberately kept afterwards |
| `rds-canvas-install.log` | canvas-ds theme installer |

## Control Center – `/storage/.config/retrodualstation/`

| File | What for |
|---|---|
| `controlcenter/rds_cc.py`, `controlcenter/tour/` | Control Center, game switcher, power menu and the tour pictures |
| `controlcenter.json` | your Control Center settings (light/dark, colour, vibration …) |
| `switcher/` | game switcher list and pictures |
| `screens.cfg` | screen areas for ES (detected by the installer) |
| `lib/` | Pillow (image processing for the Artwork Manager) |
| `fastswitch` | present = fast switch on (switch at the top of the Control Center) |
| `temp-settings.json` | briefly set per-game settings (restart in DSperate), for clean-up |
| `*.done` | "already done" markers so the installer does not repeat one-time steps |

(This folder gets the `rds-` prefix with the next ES build.)

## Backups

| File | What for |
|---|---|
| `/storage/roms/backup/rds-original-backup.zip` + `.txt` | emergency copy of your settings from before RDS (ROCKNIX backup format) with instructions |
| `/storage/.config/rds-backup/rds-original-backup.zip` | the same copy internally – for the automatic restore at start |
| `/storage/.config/rds-uninstall.running` | only during uninstall: if it is interrupted, the next start restores the backup |

## Services and system – `/storage/.config/`

| File | What for |
|---|---|
| `system.d/rds-controlcenter.service` | starts the Control Center with ES (dual mode only) |
| `system.d/rds-resume.service` | closes the power menu after waking up |
| `system.d/rds-uninstall-guard.service` | uninstall safety net (see above) |
| `system.d/essway.service.d/rds-dual.conf` | present = dual mode (ES starts through RDS) |
| `logind.conf.d/rds-logind-powerkey.conf` | in dual mode the power button belongs to the Control Center |
| `sway/config`, `mako/config` | single lines marked "RetroDualStation" (keyboard devices, volume pop-up off) |

## Ports – `/storage/roms/ports/`

| File | What for |
|---|---|
| `RDS Dual-Screen.sh`, `RDS Single-Screen.sh` | switch mode |
| `RDS Artwork Manager.sh`, `rds-artworkmanager/` | Artwork Manager – program and **your data** (settings, backups, own images) |
| `Uninstall RDS.sh` | uninstall |
| `Install RDS.sh`, `.dualstation/` | only the downloaded package – gone after installing; a new package shows up as **Update RDS** |
| `images/rds-*.png` | icons of the entries |

## Themes – `/storage/.config/emulationstation/themes/`

`canvas-rds` and `dii-ess-aye-rds` – themes for both screens (names stay, otherwise the theme selection would be lost).

## Next to your save states

| File | What for |
|---|---|
| `roms/savestates/nds/*.dss.png` | slot previews for DraStic and DSperate (RetroArch creates its own) |

## Only until restart – `/tmp/`

`rds-frozen.json` (parked game during fast switch), `rds-next-launch` (request to ES), `rds-gs-timing.json` (test
timings), `rds-shot` and other `rds-*` files for tests.

## Changed settings (no files of their own)

The installer changes single entries in `retroarch.cfg`, `drastic.cfg`, `dsperate.ini`, `es_settings.cfg`,
`es_input.cfg` (RG DS Plus) and `system.cfg` – e.g. shortcuts, hidden notifications, slot 1 for saving by hand.
The original values are kept in `settings-before-rds.json`; uninstalling restores them.

Technical details: [TECHNICAL.md](https://github.com/Ninte86hl/RetroDualStation/blob/main/docs/TECHNICAL.md)
