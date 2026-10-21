# Credits

RetroDualStation (RDS) is only a small layer on top of the work of many people.
Thank you to everyone who made it possible.

## Operating system and EmulationStation

- **[ROCKNIX](https://github.com/ROCKNIX) team and contributors** – the
  ROCKNIX distribution, its build system and
  [emulationstation-next](https://github.com/ROCKNIX/emulationstation-next),
  which this patch is based on. Also for the dual-screen groundwork for the
  RG DS family (Sway setup, `lowerdeck`, `vertical-check`).
- **[Batocera](https://github.com/batocera-linux) team and contributors** –
  batocera-emulationstation, the foundation of the ROCKNIX EmulationStation.
- **Alec "Aloshi" Lofquist and contributors** – the original
  [EmulationStation](https://emulationstation.org).

## Themes – the two that made RDS possible

RDS ships two themes, and both carry their creators' names on purpose:
**dii-ess-aye rds** and **canvas rds** are our adaptations, but the ideas, the designs and
countless hours of work behind them belong to beebono and toniremi.

### dii-ess-aye rds – thanks to beebono

- **[beebono](https://github.com/beebono)** created
  [dii-ess-aye](https://github.com/beebono/dii-ess-aye), a dual-screen theme
  for the RG DS (and AYN Thor). RDS started from it: the game list below and artwork
  above, on one device with two screens – this theme showed how good that can look.
  beebono also added a license so the adaptation can be shared – thank you!
- `dii-ess-aye-rds` is the adaptation for RDS by [Ninte86hl](https://github.com/Ninte86hl).
- Credited in the theme itself: **Ant ([anthonycaccese](https://github.com/anthonycaccese))**
  for the status and slot icons, **Jeod ([JeodC](https://github.com/JeodC))**
  for testing, **Zoidburg13** for the system icons.

dii-ess-aye is licensed under the **MIT License**
(Copyright (c) 2026 Noxwell / beebono). Thank you, beebono, for adding the
license and allowing the RG DS Plus variant to be shared! The variant is
included in [`theme/dii-ess-aye-rds/`](theme/dii-ess-aye-rds/)
with the original license and copyright notice. The original also credits
**Valve** for the Steam logo (Wikimedia Commons).

### canvas rds – thanks to toniremi

- **[toniremi](https://github.com/toniremi)** created [canvas-ds](https://github.com/toniremi/canvas-ds),
  the beautiful dual-screen theme that is RDS's default look: five game list views, hero images
  and video on top. toniremi allowed the adaptation to be shared and bundled with RDS –
  thank you for your generosity and for a theme that makes two screens feel natural!
- `canvas-rds` is canvas-ds with a small overlay for RDS
  ([`theme/canvas-rds-overlay/`](theme/canvas-rds-overlay/)).
- **[Siddy212](https://github.com/Siddy212)** – [Canvas (ES version)](https://github.com/Siddy212/canvas-es),
  the original theme canvas-ds is built on.
- **[fagnerpc](https://github.com/fagnerpc)** – original artwork and layouts.
- **Zoidburg13** – system icons.

canvas-ds is licensed under **CC BY-NC-SA**; the overlay is shared under the
same terms. Only the 7 changed layout files are included – the theme itself
comes from the original project.

## Libraries and tools

- **[Sway](https://swaywm.org) / wlroots** – the Wayland compositor that
  makes the dual-screen layout possible.
- **[SDL](https://www.libsdl.org)** – used by EmulationStation for video and input.

## Hardware

- **Anbernic** – for the RG DS and RG DS Plus.

---

Missing someone? Please open an issue and I'll add them.
