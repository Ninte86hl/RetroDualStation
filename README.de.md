# RetroDualStation

**One system, two screens, everything in sync.**

Dual-Screen-EmulationStation für das **Anbernic RG DS Plus**, aufgebaut auf **ROCKNIX**.
*Früher „ROCKNIX DualStation“.*

🇬🇧 [English version](README.md)

![canvas-ds mit RetroDualStation: Systemansicht über beide Bildschirme](docs/screenshots/canvas-system.png)

---

## Was ist RetroDualStation?

ROCKNIX zeigt EmulationStation auf dem RG DS Plus normalerweise auf einem Bildschirm.
RetroDualStation nutzt **beide Bildschirme** (2048 × 768): oben Artwork und Video,
Spieleliste und Menüs dort, wo sie hingehören – auch nach Spielen und Neustarts.
Ein freies Add-on: Installation über **Ports**, zurück zum Original-ES mit einem Tipp.

## Was ist anders?

| | ROCKNIX Standard | RetroDualStation |
|---|---|---|
| EmulationStation | ein Bildschirm | **beide Bildschirme** |
| Themes | ein Bildschirm | Dual-Screen-Themes wie **canvas-ds** |
| Artwork | Scraper-Bilder | Hero, Icon und Cover pro Spiel über **DualStation Sync** |
| Unterer Bildschirm im Spiel | nur RetroArch-Touchmenü | **Kontrollcenter** überall – ES, RetroArch, DraStic, DSperate, PortMaster |
| Zurück zum Original | – | ein Tipp unter **Ports** |

## Was wir bieten

- **Dual-Screen-ES** – Menüs, Scraper, Tastatur und Meldungen auf dem richtigen Bildschirm
- **canvas-ds** – fünf Spielelisten-Ansichten für zwei Bildschirme
- **DualStation Sync** – PC-Begleiter für Dual-Screen-Artwork *(siehe unten)*
- **Kontrollcenter** – Schnelleinstellungen, Power-Menü und Spiel beenden über jedem Spiel
- **Gameswitcher** – zwischen den zuletzt gespielten Spielen wechseln und dort weitermachen

## Themes

### canvas-ds

[canvas-ds](https://github.com/toniremi/canvas-ds) von toniremi, angepasst über ein kleines Overlay
(mit seiner Erlaubnis, CC BY-NC-SA). Oben: Hero-Bild, nach 5 Sekunden blendet das Video ein.

| | |
|---|---|
| ![Gamecarousel](docs/screenshots/canvas-view-gamecarousel.png) | ![Detailliert](docs/screenshots/canvas-view-detailed.png) |
| **Gamecarousel** – Icons nebeneinander | **Detailliert** – Cover, Beschreibung und Infos |
| ![Raster](docs/screenshots/canvas-view-grid.png) | ![Showcase](docs/screenshots/canvas-view-showcase.png) |
| **Raster** – Cover füllen den unteren Bildschirm | **Showcase** – Cover und Spieleliste |
| ![Spotlight](docs/screenshots/canvas-view-spotlight.png) | |
| **Spotlight** – eine große Karte, die hereingleitet | |

Artwork: `romname-hero.png`, `romname-icon.png`, `romname-box.png` und das Scraper-Logo –
die ersten drei erstellt DualStation Sync für dich; fehlende Bilder ersetzt ES durch Scraper-Medien.

## DualStation Sync

Unser PC-Begleiter (derzeit noch als
[RocknixDS Artwork Manager](https://github.com/Ninte86hl/RocknixDS-Artwork-Manager) veröffentlicht):
bereitet Hero-, Icon- und Coverbilder für deine Spiele in den Namen und Größen vor, die canvas-ds erwartet.

## Kontrollcenter

Die **Anbernic-Taste** öffnet ein Kontrollcenter auf dem unteren Bildschirm – über ES, RetroArch,
DraStic, DSperate und PortMaster. Das Spiel pausiert und läuft danach an derselben Stelle weiter.

- **Schnelleinstellungen** – Helligkeit beider Bildschirme, Lautstärke, Leistung, WLAN, Bluetooth
- **Spiel beenden** – keine Tastenkürzel mehr merken
- **Unterer Screen aus** – DS-Spiele auf einem Bildschirm spielen; die Anbernic-Taste schaltet ihn
  wieder ein. In RetroArch und PortMaster wird der untere Bildschirm automatisch dunkel.
- **Power-Menü** – kurz auf die **Ein/Aus-Taste**: Ruhemodus, Neu starten (wahlweise mit
  Log-Sicherung), Ausschalten, ES neu starten
- Deutsch oder Englisch, je nach ES-Sprache

| | |
|---|---|
| ![Kontrollcenter](docs/screenshots/control-center-main.png) | ![WLAN](docs/screenshots/control-center-wifi.png) |
| **Kontrollcenter** über einem pausierten Spiel | **WLAN** – gespeicherte Netze oben |
| ![Bluetooth](docs/screenshots/control-center-bluetooth.png) | ![Tastatur](docs/screenshots/control-center-keyboard.png) |
| **Bluetooth** – Controller direkt koppeln | **Bildschirmtastatur** für Passwörter |
| ![Power-Menü](docs/screenshots/control-center-power.png) | |
| **Power-Menü** – kurz auf die Ein/Aus-Taste | |

## Gameswitcher

**Home-Taste halten** (1,5 s) zeigt die zuletzt gespielten Spiele – jedes mit einem Bild vom letzten
Stand im Format seiner Konsole. **A** setzt genau dort fort, **Y** startet neu, **X** entfernt es aus
der Liste. **Kurz drücken** speichert und kehrt zu ES zurück.

Funktioniert mit RetroArch, DraStic, DSperate und PortMaster. Ein Wechsel dauert etwa 5 Sekunden –
ein Ladebildschirm liegt über beiden Screens, der Ton bleibt stumm, bis du wieder im Spiel bist.

![Gameswitcher](docs/screenshots/game-switcher.png)

## Roadmap

| Stand | Was |
|---|---|
| ✅ | Dual-Screen-EmulationStation, Installer, Rückweg mit einem Tipp |
| ✅ | canvas-ds mit fünf Spielelisten-Ansichten |
| ✅ | DualStation Sync: Dual-Screen-Artwork |
| ✅ | Kontrollcenter: Schnelleinstellungen, WLAN, Bluetooth, Tastatur, Power-Menü, Spiel beenden, unterer Screen aus |
| ✅ | Gameswitcher – zuletzt gespielte Spiele mit Screenshot vom letzten Stand; **A** weiterspielen, **Y** neu starten *(ab v11)* |
| 🔜 **als Nächstes** | Kontrollcenter: Seite „Spiel“ – Speicherstände und Tastenkürzel |
| 🔜 | Unterstützung für das normale RG DS |
| 💭 vielleicht | Einstellungsmenü wie am Smartphone, aufgerufen aus dem Kontrollcenter |
| 💭 vielleicht | RetroAchievements – Benachrichtigung und Übersicht |
| 💭 vielleicht | Benutzerprofile mit eigenen Spielständen |
| 💭 vielleicht | DraStic: großes Pausemenü und eigene Einstellungsoberfläche |
| 🕓 später | DualStation Sync: bessere Titelsuche, Spielelisten bearbeiten |

## Installation

1. **`rocknix-dualstation-v10.zip`** (enthält canvas-ds) aus dem
   [aktuellen Release](https://github.com/Ninte86hl/rocknix-dualstation/releases/latest) laden.
2. In den Ordner **`ports`** bei den ROMs entpacken (`/storage/roms/ports`).
3. In ES **Ports** → **Install ROCKNIX DualStation** starten.

Der Installer prüft vorher Gerät und ROCKNIX-Version und verändert nichts, wenn sie nicht passen.
Danach stehen unter **Ports** *RGDS Dual-Screen ES*, *RGDS Single-Screen ES* und *Uninstall*.
Ein Update funktioniert genauso.

<details>
<summary>ROMs auf einer ext4-Partition? ZIP über das Netzwerk kopieren</summary>

```bash
scp rocknix-dualstation-v10.zip root@<IP>:/storage/roms/ports/
```
```bash
ssh root@<IP> "cd /storage/roms/ports && unzip rocknix-dualstation-v10.zip && rm rocknix-dualstation-v10.zip"
```
</details>

**Deinstallation:** *Ports → Uninstall ROCKNIX DualStation* stellt das Original-ES samt Theme wieder her.
Spiele, Medien, Spielelisten und Spielstände bleiben unberührt.

## Gut zu wissen

- **Kein ScreenScraper und keine RetroAchievements** in der Dual-Version – die Zugangsdaten
  gibt es nur für den offiziellen ROCKNIX-Build. Zum Scrapen per Ports auf *Single* und zurück.
- DS über RetroArch-Cores ist ungetestet; DraStic und DSperate funktionieren.
- Touch in DraStic reagiert nicht? **Follow 3D Renderer** auf *Auto* stellen (auch im Original-ROCKNIX).

Technik, manuelle Installation und wie es funktioniert: [docs/TECHNIK.md](docs/TECHNIK.md)

## Danksagung & Lizenz

Aufgebaut auf der Arbeit der ROCKNIX- und Batocera-Teams, dem ursprünglichen EmulationStation,
canvas-ds von toniremi und dii-ess-aye von beebono. Vollständige Liste: [CREDITS.md](CREDITS.md). Danke! 🙏

Skripte und Dokumentation: MIT ([LICENSE](LICENSE)). Der ES-Patch ändert
[ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next) (MIT).
Auf Screenshots sichtbare Logos und Grafiken gehören ihren jeweiligen Eigentümern.
