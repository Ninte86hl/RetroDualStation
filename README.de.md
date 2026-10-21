# RetroDualStation

**One system, two screens, everything in sync.**

Dual-Screen-EmulationStation für das **Anbernic RG DS Plus**, aufgebaut auf **ROCKNIX**.
*Früher „ROCKNIX DualStation“.*

🇬🇧 [English version](README.md) · 🧭 [Kurze Tour](docs/TOUR.de.md)

---

## Was ist RetroDualStation?

ROCKNIX zeigt EmulationStation auf dem RG DS Plus normalerweise auf einem Bildschirm.
RetroDualStation nutzt **beide Bildschirme** (2048 × 768): oben Artwork und Video,
Spieleliste und Menüs dort, wo sie hingehören – auch nach Spielen und Neustarts.
Ein freies Add-on: Installation über **Ports**, zurück zum Original-ES mit einem Tipp.

## Galerie

*Zum Umschalten auf einen Titel tippen.*

<details open>
<summary><b>Kontrollcenter</b></summary>

<p align="center"><img src="docs/screenshots/cc-unten.png" alt="Kontrollcenter" width="400"> <img src="docs/tour/tour-spiel.png" alt="Seite „Spiel“" width="400"></p>

**Anbernic-Taste** – Schnelleinstellungen, Speicherplätze mit Bild, Vorspulen, Power-Menü – über jedem Spiel. → [mehr](https://github.com/Ninte86hl/rocknix-dualstation/wiki/Kontrollcenter)

</details>

<details>
<summary><b>Gameswitcher</b></summary>

<p align="center"><img src="docs/screenshots/gs-unten.png" alt="Gameswitcher" width="480"></p>

**Home halten** – zwischen den letzten Spielen wechseln und genau dort weitermachen. → [mehr](https://github.com/Ninte86hl/rocknix-dualstation/wiki/Gameswitcher)

</details>

<details>
<summary><b>RetroAchievements</b></summary>

<p align="center"><img src="docs/tour/tour-ra.png" alt="RetroAchievements" width="480"></p>

Fortschritt und alle Erfolge im Kontrollcenter, Meldung oben über dem Spiel. → [mehr](https://github.com/Ninte86hl/rocknix-dualstation/wiki/RetroAchievements-DE)

</details>

📖 Alle Funktionen, Tasten und Tipps: **[Wiki](https://github.com/Ninte86hl/rocknix-dualstation/wiki/Home-DE)** · [Roadmap](https://github.com/Ninte86hl/rocknix-dualstation/wiki/Roadmap-DE) · [Gut zu wissen](https://github.com/Ninte86hl/rocknix-dualstation/wiki/Gut-zu-wissen)

## Was ist anders?

| | ROCKNIX Standard | RetroDualStation |
|---|---|---|
| EmulationStation | ein Bildschirm | **beide Bildschirme** |
| Themes | ein Bildschirm | Dual-Screen-Themes wie **[canvas-ds](https://github.com/Ninte86hl/rocknix-dualstation/wiki/Themes-DE)** |
| Artwork | Scraper-Bilder | Boxart, Icon und Hero pro Spiel über den **Artwork Manager** – direkt am Gerät |
| Unterer Bildschirm im Spiel | nur RetroArch-Touchmenü | **Kontrollcenter** überall – ES, RetroArch, DraStic, DSperate, PortMaster |
| Zurück zum Original | – | ein Tipp unter **Ports** |

## Installation

1. **`rocknix-dualstation-v13.1.zip`** (enthält canvas-ds) aus dem
   [aktuellen Release](https://github.com/Ninte86hl/rocknix-dualstation/releases/latest) laden.
2. In den Ordner **`ports`** bei den ROMs entpacken (`/storage/roms/ports`).
3. In ES **Ports** → **Install ROCKNIX DualStation** starten.

Der Installer prüft vorher Gerät und ROCKNIX-Version und verändert nichts, wenn sie nicht passen.
Danach stehen unter **Ports** *RGDS Dual-Screen ES*, *RGDS Single-Screen ES* und *Uninstall*.
Ein Update funktioniert genauso.

<details>
<summary>ROMs auf einer ext4-Partition? ZIP über das Netzwerk kopieren</summary>

```bash
scp rocknix-dualstation-v13.1.zip root@<IP>:/storage/roms/ports/
```
```bash
ssh root@<IP> "cd /storage/roms/ports && unzip rocknix-dualstation-v13.1.zip && rm rocknix-dualstation-v13.1.zip"
```
</details>

**Deinstallation:** *Ports → Uninstall ROCKNIX DualStation* stellt das Original-ES samt Theme wieder her.
Spiele, Medien, Spielelisten und Spielstände bleiben unberührt.

Technik und manuelle Installation: [docs/TECHNIK.md](docs/TECHNIK.md)

## Danksagung & Lizenz

Aufgebaut auf der Arbeit der ROCKNIX- und Batocera-Teams, dem ursprünglichen EmulationStation,
canvas-ds von toniremi und dii-ess-aye von beebono. Vollständige Liste: [CREDITS.md](CREDITS.md). Danke! 🙏

Skripte und Dokumentation: MIT ([LICENSE](LICENSE)). Der ES-Patch ändert
[ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next) (MIT).
Auf Screenshots sichtbare Logos und Grafiken gehören ihren jeweiligen Eigentümern.
