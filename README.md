# RetroDualStation

**One system, two screens, everything in sync.**

Dual-screen EmulationStation for the **Anbernic RG DS Plus**, built on **ROCKNIX**.
*Formerly “ROCKNIX DualStation”.*

🇩🇪 [Deutsche Version](README.de.md) · 🧭 [Quick tour](docs/TOUR.md)

<p align="center"><img src="docs/screenshots/canvas-system.png" alt="canvas-ds on RetroDualStation: system view on both screens" width="360"></p>

---

## What is RetroDualStation?

Stock ROCKNIX runs EmulationStation on one screen of the RG DS Plus.
RetroDualStation stretches it across **both screens** (2048 × 768): artwork and video on top,
your game list and menus where they belong – and it stays that way after games and reboots.
It is a free, open add-on: install it via **Ports**, switch back to stock ES with one tap.

## What's different?

| | Stock ROCKNIX | RetroDualStation |
|---|---|---|
| EmulationStation | one screen | **both screens** |
| Themes | single-screen | dual-screen themes like **canvas-ds** |
| Artwork | scraper images | boxart, icon and hero per game via the **Artwork Manager** – right on the device |
| Bottom screen in games | RetroArch touch menu only | **Control Center** everywhere – ES, RetroArch, DraStic, DSperate, PortMaster |
| Going back | – | one tap in **Ports** |

## Highlights

- **[Control Center](https://github.com/Ninte86hl/rocknix-dualstation/wiki/Control-Center)** – Anbernic button: quick settings, save slots with pictures, fast forward, power menu – over any game
- **[Game switcher](https://github.com/Ninte86hl/rocknix-dualstation/wiki/Game-Switcher)** – hold Home: jump between recent games and continue
- **[RetroAchievements](https://github.com/Ninte86hl/rocknix-dualstation/wiki/RetroAchievements)** – progress in the Control Center, notification on top of the game
- **[canvas-ds](https://github.com/Ninte86hl/rocknix-dualstation/wiki/Themes)** – five game list views made for two screens
- **[Artwork Manager](https://github.com/Ninte86hl/rocknix-dualstation/wiki/Artwork-Manager)** – boxart, icon and hero right on the device
- **Game search** – **Y** in the system view · **Quick tour** – **Select** in the Control Center

| | | |
|:-:|:-:|:-:|
| <img src="docs/screenshots/control-center-main.png" alt="Control Center"> | <img src="docs/screenshots/game-switcher.png" alt="Game switcher"> | <img src="docs/screenshots/canvas-view-gamecarousel.png" alt="canvas-ds"> |
| **Control Center** | **Game switcher** | **canvas-ds** |

📖 All features, buttons and tips: **[Wiki](https://github.com/Ninte86hl/rocknix-dualstation/wiki)** · [Roadmap](https://github.com/Ninte86hl/rocknix-dualstation/wiki/Roadmap) · [Good to know](https://github.com/Ninte86hl/rocknix-dualstation/wiki/Good-to-know)

## Installation

1. Download **`rocknix-dualstation-v13.1.zip`** (includes canvas-ds) from the
   [latest release](https://github.com/Ninte86hl/rocknix-dualstation/releases/latest).
2. Unpack it into the **`ports`** folder of your ROMs (`/storage/roms/ports`).
3. In ES open **Ports** → **Install ROCKNIX DualStation**.

The installer checks your device and ROCKNIX version first and changes nothing if they don't match.
Afterwards **Ports** has *RGDS Dual-Screen ES*, *RGDS Single-Screen ES* and *Uninstall*.
Updating works the same way.

<details>
<summary>ROMs on an ext4 partition? Copy the ZIP over the network</summary>

```bash
scp rocknix-dualstation-v13.1.zip root@<IP>:/storage/roms/ports/
```
```bash
ssh root@<IP> "cd /storage/roms/ports && unzip rocknix-dualstation-v13.1.zip && rm rocknix-dualstation-v13.1.zip"
```
</details>

**Uninstall:** *Ports → Uninstall ROCKNIX DualStation* restores stock ES and its theme.
Games, media, game lists and saves are not touched.

Technical details and manual installation: [docs/TECHNICAL.md](docs/TECHNICAL.md)

## Credits & license

Built on the work of the ROCKNIX and Batocera teams, the original EmulationStation,
toniremi's canvas-ds and beebono's dii-ess-aye. Full list: [CREDITS.md](CREDITS.md). Thank you! 🙏

Scripts and documentation: MIT ([LICENSE](LICENSE)). The ES patch modifies
[ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next) (MIT).
Logos and artwork in screenshots belong to their respective owners.
