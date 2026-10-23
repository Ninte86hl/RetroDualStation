# RetroDualStation

**One system, two screens, everything in sync.**

Dual-screen EmulationStation for the **Anbernic RG DS Plus** and **RG DS**, built on **ROCKNIX**.
*Formerly “ROCKNIX DualStation”.*

🇩🇪 [Deutsche Version](README.de.md) · 🧭 [Quick tour](https://github.com/Ninte86hl/RetroDualStation/wiki/Tour)

<p align="center"><img src="docs/screenshots/rds-mockup.webp" alt="RetroDualStation on a dual-screen handheld" width="440"></p>

---

## What is RetroDualStation?

Stock ROCKNIX runs EmulationStation on one screen of the RG DS Plus and RG DS.
RetroDualStation stretches it across **both screens**: artwork and video on top,
your game list and menus where they belong – and it stays that way after games and reboots.
It is a free, open add-on: install it via **Ports**, switch back to stock ES with one tap.

## Gallery

*Tap a title to switch.*

<details open>
<summary><b>Control Center</b></summary>

<p align="center"><img src="docs/screenshots/cc-unten.png" alt="Control Center" width="400"> <img src="docs/tour/tour-spiel.png" alt="Game page" width="400"></p>

**Anbernic button** – quick settings, save slots with pictures, fast forward, power menu – over any game. → [more](https://github.com/Ninte86hl/RetroDualStation/wiki/Control-Center)

</details>

<details>
<summary><b>Game switcher</b></summary>

<p align="center"><img src="docs/screenshots/gs-unten.png" alt="Game switcher" width="480"></p>

**Hold Home** – jump between recent games and continue exactly where you left off. A switch takes about 5 seconds: every game is started through ES as usual, so the emulator loads fresh each time. → [more](https://github.com/Ninte86hl/RetroDualStation/wiki/Game-Switcher)

</details>

<details>
<summary><b>RetroAchievements</b></summary>

<p align="center"><img src="docs/tour/tour-ra.png" alt="RetroAchievements" width="480"></p>

Progress and all achievements in the Control Center, notification on top of the game. → [more](https://github.com/Ninte86hl/RetroDualStation/wiki/RetroAchievements)

</details>

🧭 **New here? The [quick tour](https://github.com/Ninte86hl/RetroDualStation/wiki/Tour) shows all buttons and features in a few minutes.**

📖 All features, buttons and tips: **[Wiki](https://github.com/Ninte86hl/RetroDualStation/wiki)** · [Roadmap](https://github.com/Ninte86hl/RetroDualStation/wiki/Roadmap) · [Good to know](https://github.com/Ninte86hl/RetroDualStation/wiki/Good-to-know)

## What's different?

| | Stock ROCKNIX | RetroDualStation |
|---|---|---|
| EmulationStation | one screen | **both screens** |
| Themes | single-screen | dual-screen themes like **[canvas-ds](https://github.com/Ninte86hl/RetroDualStation/wiki/Themes)** |
| Artwork | scraper images | boxart, icon and hero per game via the **Artwork Manager** – right on the device |
| Bottom screen in games | RetroArch touch menu only | **Control Center** everywhere – ES, RetroArch, DraStic, DSperate, PortMaster |
| Going back | – | one tap in **Ports** |

## Installation

1. Download **`retrodualstation-v15.1.zip`** (includes canvas-ds) from the [latest release](https://github.com/Ninte86hl/RetroDualStation/releases/latest).
2. Unpack it into the **`ports`** folder of your ROMs (`/storage/roms/ports`).
3. In ES open **Ports** → <img src="docs/icons/rds-install.png" width="24"> **Install RDS**.

The installer checks your device and ROCKNIX version first and changes nothing if they don't match.
Updating works the same way. Afterwards **Ports** has:

| | Entry | What for |
|:-:|---|---|
| <img src="docs/icons/rds-install.png" width="48"> | **Install RDS** | Installs or updates RDS |
| <img src="docs/icons/rds-dual.png" width="48"> | **RDS Dual-Screen** | ES across both screens |
| <img src="docs/icons/rds-single.png" width="48"> | **RDS Single-Screen** | Stock ES on one screen |
| <img src="docs/icons/rds-artwork.png" width="48"> | **Artwork Manager** | Boxart, icons and hero images on the device |
| <img src="docs/icons/rds-uninstall.png" width="48"> | **Uninstall RDS** | Back to stock; games and saves stay |

<details>
<summary>ROMs on an ext4 partition? Copy the ZIP over the network</summary>

```bash
scp retrodualstation-v15.1.zip root@<IP>:/storage/roms/ports/
```
```bash
ssh root@<IP> "cd /storage/roms/ports && unzip retrodualstation-v15.1.zip && rm retrodualstation-v15.1.zip"
```
</details>

Technical details and manual installation: [docs/TECHNICAL.md](docs/TECHNICAL.md)

## Credits & license

A special thank-you goes to the two theme creators – RDS wouldn't look like this without them:

- **[beebono](https://github.com/beebono)** for [dii-ess-aye](https://github.com/beebono/dii-ess-aye) – the dual-screen theme for the RG DS that RDS started from. Included as **dii-ess-aye rds**.
- **[toniremi](https://github.com/toniremi)** for [canvas-ds](https://github.com/toniremi/canvas-ds) – RDS's default theme with five views, hero image and video. Included as **canvas rds**, shared with his permission.

Both themes keep their names on purpose. Thank you! 🙏

Also built on the work of the ROCKNIX and Batocera teams and the original EmulationStation.
Full list: [CREDITS.md](CREDITS.md).

Scripts and documentation: MIT ([LICENSE](LICENSE)). The ES patch modifies
[ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next) (MIT).
Logos and artwork in screenshots belong to their respective owners.
