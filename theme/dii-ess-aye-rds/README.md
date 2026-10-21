# dii-ess-aye-rds

RG DS Plus variant of **[dii-ess-aye](https://github.com/beebono/dii-ess-aye)**
by **beebono**, adapted by [Ninte86hl](https://github.com/Ninte86hl) for the
dual-screen EmulationStation of this repository.

> 🇩🇪 RG-DS-Plus-Variante des Themes dii-ess-aye von beebono, angepasst
> für die Dual-Screen-EmulationStation dieses Repositorys. Installation
> siehe [`../../README.de.md`](../../README.de.md).

## Changes from the original

| | Original (RG DS) | This variant (RG DS Plus) |
|---|---|---|
| Canvas | 1920 × 480 (three 640 × 480 areas, the third unused) | 2048 × 768 (two 1024 × 768 screens) |
| Top screen | X 0 – 0.333 | X 0 – 0.5 |
| Bottom screen | X 0.333 – 0.666 | X 0.5 – 1.0 |
| `theme.xml` | picks RG DS or Thor layout by screen width | always loads `theme-rgds.xml` |

All positions and sizes in `theme-rgds.xml` were scaled to the new canvas,
including the **Prev/Next** (L/R) tabs, which stay on the top screen as in
the original. All assets (images, icons, font, sounds) are unchanged.

Not included (see the original project if you need them):

- `scripts/` – the original enable script rewrites the Sway config and
  replaces the ES start script for the RG DS. **Do not use it with this
  mod**; the mod handles Sway and the ES start itself.
- `theme-thor.xml` and the preview images.

## Requirements

Needs the dual-screen ES from this repository (ES window 2048 × 768 across
both screens). With stock ROCKNIX ES both halves are squeezed onto the top
screen.

## Installation

Copy this folder to the device:

```bash
scp -r theme/dii-ess-aye-rds root@<IP>:/storage/.config/emulationstation/themes/
```

Then select **dii-ess-aye-rds** under *User Interface Settings → Theme*,
or switch to the dual-screen mode via Ports – the switch sets the theme
automatically.

## Credits and license

- Original theme: **beebono** – MIT License, Copyright (c) 2026 Noxwell.
  See [`LICENSE`](LICENSE) (unchanged original).
- Credited in the original theme: **Ant (anthonycaccese)** for the status and
  slot icons, **Jeod (JeodC)** for testing the Thor variant, **Zoidburg13**
  for the system icons, **Valve** for the Steam logo (Wikimedia Commons).
- RG DS Plus adaptation: Ninte86hl, provided under the same MIT License.
