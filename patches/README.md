# Patches

Hier liegt der EmulationStation-Patch für das ROCKNIX-Buildsystem:

- `001-rgds-menu-dualscreen-v2.patch` – gegen
  [ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next)
  Commit `cada856d86e3115fbbf0bce09dd761b0ee8fa9fd`

## Verwenden

Den Patch nach

```
distribution/projects/ROCKNIX/packages/ui/emulationstation/patches/aarch64/
```

kopieren und das Paket bauen (siehe [`../docs/BUILD.md`](../docs/BUILD.md)).

In diesem Ordner darf **nur eine** Patch-Datei liegen. Eine zweite Datei
würde beim Build zusätzlich angewendet und dabei fehlschlagen.

## Aktualisieren

Nach Änderungen am Quellcode in `emulationstation-next`:

```bash
git diff > /pfad/zu/diesem/repo/patches/001-rgds-menu-dualscreen-v2.patch
```

Unversionierte Hilfsdateien (z. B. `Renderer.cpp.rgds-backup`) erfasst
`git diff` nicht. Das ist gewollt.
