# Patches

Against [ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next)
commit `cada856d86e3115fbbf0bce09dd761b0ee8fa9fd`:

- `001-rgds-menu-dualscreen.patch` – menus, popups and keyboard on the right screen
- `002-rds-gameswitcher-chain.patch` – Game switcher: start the next game right after the
  current one ends, without rebuilding ES (request file `/tmp/rds-next-launch`)

## Usage

Copy the patch to

```
distribution/projects/ROCKNIX/packages/ui/emulationstation/patches/aarch64/
```

and build the package (see [`../docs/BUILD.md`](../docs/BUILD.md)).

Copy **both** patches. Remove older copies (e.g. `001-rgds-menu-dualscreen-v2.patch`)
first – every file in that folder is applied.

## Updating

After changing the source in `emulationstation-next`:

```bash
git diff > /path/to/this/repo/patches/001-rgds-menu-dualscreen.patch
```

Untracked helper files (e.g. `Renderer.cpp.rgds-backup`) are not included
by `git diff`. This is intended.
