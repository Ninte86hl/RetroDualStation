# Patches

Against [ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next)
commit `cada856d86e3115fbbf0bce09dd761b0ee8fa9fd`:

- `001-rgds-menu-dualscreen.patch` – menus, popups and keyboard on the right screen
- `002-rds-gameswitcher-chain.patch` – Game switcher: start the next game right after the
  current one ends, without rebuilding ES (request file `/tmp/rds-next-launch`)
- `003-rds-bluetooth-systemcfg-navbar.patch` – Bluetooth pairing window on one screen; ES re-reads
  `system.cfg` when the main menu opens and the file was changed (e.g. by the Control Center);
  B in the system list no longer opens the navigation bar ("Go to manufacturer");
  Y in the system list searches games across all systems (result list, A jumps to the game) –
  no "All games" collection needed.
- `004-rds-screens.patch` – screen areas: replaces the fixed 2048 × 768 / 1024 values with
  `RdsScreens` (`es-core/src/RdsScreens.h`), read from `/storage/.config/retrodualstation/screens.cfg`.
  Without the file the RG DS Plus layout is used – same behaviour as before.
- `005-rds-theme-screen-vars.patch` – theme variables for the screen areas
  (`${screen.top.relx}`, `${screen.bottom.relwidth}`, … – see [docs/THEMES.md](../docs/THEMES.md)).

## Usage

Copy the patch to

```
distribution/projects/ROCKNIX/packages/ui/emulationstation/patches/aarch64/
```

and build the package (see [`../docs/BUILD.md`](../docs/BUILD.md)).

Copy **all five** patches. Remove older copies (e.g. `001-rgds-menu-dualscreen-v2.patch`)
first – every file in that folder is applied.

## Updating

After changing the source in `emulationstation-next`:

```bash
git diff > /path/to/this/repo/patches/001-rgds-menu-dualscreen.patch
```

Untracked helper files (e.g. `Renderer.cpp.rgds-backup`) are not included
by `git diff`. This is intended.
