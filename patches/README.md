# Patches

- `001-rgds-menu-dualscreen.patch` – against
  [ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next)
  commit `cada856d86e3115fbbf0bce09dd761b0ee8fa9fd`

## Usage

Copy the patch to

```
distribution/projects/ROCKNIX/packages/ui/emulationstation/patches/aarch64/
```

and build the package (see [`../docs/BUILD.md`](../docs/BUILD.md)).

That folder must contain **only one** patch file. A second file would be
applied as well and fail.

## Updating

After changing the source in `emulationstation-next`:

```bash
git diff > /path/to/this/repo/patches/001-rgds-menu-dualscreen.patch
```

Untracked helper files (e.g. `Renderer.cpp.rgds-backup`) are not included
by `git diff`. This is intended.
