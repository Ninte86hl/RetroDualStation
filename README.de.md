# RetroDualStation

**One system, two screens, everything in sync.**

Dual-Screen-EmulationStation für das **Anbernic RG DS Plus**, aufgebaut auf **ROCKNIX**.
*Früher „ROCKNIX DualStation“.*

🇬🇧 [English version](README.md) · 🧭 [Kurze Tour](docs/TOUR.de.md)

<p align="center"><img src="docs/screenshots/canvas-system.png" alt="canvas-ds mit RetroDualStation: Systemansicht auf beiden Bildschirmen" width="360"></p>

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
| Artwork | Scraper-Bilder | Boxart, Icon und Hero pro Spiel über den **Artwork Manager** – direkt am Gerät |
| Unterer Bildschirm im Spiel | nur RetroArch-Touchmenü | **Kontrollcenter** überall – ES, RetroArch, DraStic, DSperate, PortMaster |
| Zurück zum Original | – | ein Tipp unter **Ports** |

## Was wir bieten

- **Dual-Screen-ES** – Menüs, Scraper, Tastatur und Meldungen auf dem richtigen Bildschirm
- **canvas-ds** – fünf Spielelisten-Ansichten für zwei Bildschirme
- **Artwork Manager** – Artworks für deine Spiele direkt am Gerät suchen und anpassen *(siehe unten)*
- **Kontrollcenter** – Schnelleinstellungen, Power-Menü und Spiel beenden über jedem Spiel
- **Gameswitcher** – zwischen den zuletzt gespielten Spielen wechseln und dort weitermachen
- **Spielesuche** – **Y** in der Systemansicht durchsucht alle Systeme auf einmal
- **Kurze Tour** – läuft einmal nach der Installation, jederzeit wieder mit **Select** im Kontrollcenter

## Themes

### canvas-ds

[canvas-ds](https://github.com/toniremi/canvas-ds) von toniremi, angepasst über ein kleines Overlay
(mit seiner Erlaubnis, CC BY-NC-SA). Oben: Hero-Bild, nach 5 Sekunden blendet das Video ein.

| | | |
|:-:|:-:|:-:|
| <img src="docs/screenshots/canvas-view-gamecarousel.png" alt="Gamecarousel"> | <img src="docs/screenshots/canvas-view-detailed.png" alt="Detailliert"> | <img src="docs/screenshots/canvas-view-grid.png" alt="Raster"> |
| **Gamecarousel** – Icons nebeneinander | **Detailliert** – Cover, Beschreibung und Infos | **Raster** – Cover füllen den unteren Bildschirm |
| <img src="docs/screenshots/canvas-view-showcase.png" alt="Showcase"> | <img src="docs/screenshots/canvas-view-spotlight.png" alt="Spotlight"> |  |
| **Showcase** – Cover und Spieleliste | **Spotlight** – eine große Karte, die hereingleitet |  |

Artwork nach dem [RetroDualStation-Artwork-Standard](docs/ARTWORK.de.md): `romname-hero.png`, `romname-icon.png`, `romname-box.png` und das Scraper-Logo –
die ersten drei erstellt der Artwork Manager für dich; fehlende Bilder ersetzt ES durch Scraper-Medien.

## Artwork Manager

Start über **Ports → Artwork Manager**. Er ergänzt **Boxart**, **Cartridge-Icon** (1:1) und
**Hero-Bild** für deine Spiele – oben siehst du live, wie alles zusammen wirkt,
unten liegen Listen, Suche und Tasten.

- Quellen: iiSU-Datenbank und SteamGridDB (kostenloser API-Key in den Einstellungen) sowie
  **eigene Bilder** aus `ports/artworkmanager/eigene/`
- **Einzelsuche** (Start) oder **Mehrfachsuche** (Select) durch alle Spiele mit fehlenden Artworks
- **Icon-Editor** – macht aus jedem Icon ein 1:1-Bild mit iiSU-Rahmen (verschieben, zoomen, Rahmen wählen)
- **Filter** in der Spieleliste: alle · fehlende · keine Artworks; **Spielesuche** über alle Systeme
- **Mehrteilige Spiele** zu einem `.m3u`-Eintrag zusammenfassen (Einstellungen), Arcade-Namen aus der FBNeo-Liste
- Sicherung jeder `gamelist.xml` vor dem ersten Speichern, Wiederherstellen in den Einstellungen

Voraussetzung: Jedes System braucht eine `gamelist.xml` – einmalig mit dem Scraper im Single-Screen-Modus erstellen.
Alle Tasten: [kurze Tour](docs/TOUR.de.md#5-artwork-manager).

Die PC-Version gibt es weiterhin als
[RocknixDS Artwork Manager](https://github.com/Ninte86hl/RocknixDS-Artwork-Manager).

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

| | | |
|:-:|:-:|:-:|
| <img src="docs/screenshots/control-center-main.png" alt="Kontrollcenter"> | <img src="docs/screenshots/control-center-wifi.png" alt="WLAN"> | <img src="docs/screenshots/control-center-bluetooth.png" alt="Bluetooth"> |
| **Kontrollcenter** über einem pausierten Spiel | **WLAN** – gespeicherte Netze oben | **Bluetooth** – Controller direkt koppeln |
| <img src="docs/screenshots/control-center-keyboard.png" alt="Tastatur"> | <img src="docs/screenshots/control-center-power.png" alt="Power-Menü"> |  |
| **Bildschirmtastatur** für Passwörter | **Power-Menü** – kurz auf die Ein/Aus-Taste |  |

## Gameswitcher

**Home-Taste halten** (1,5 s) zeigt die zuletzt gespielten Spiele – jedes mit einem Bild vom letzten
Stand im Format seiner Konsole. **A** setzt genau dort fort, **Y** startet neu, **X** entfernt es aus
der Liste. **Kurz drücken** speichert und kehrt zu ES zurück, **zweimal drücken** wechselt direkt zum vorherigen Spiel.

Funktioniert mit RetroArch, DraStic, DSperate und PortMaster. Ein Wechsel dauert etwa 5 Sekunden –
ein Ladebildschirm liegt über beiden Screens, der Ton bleibt stumm, bis du wieder im Spiel bist.

<p align="center"><img src="docs/screenshots/game-switcher.png" alt="Gameswitcher" width="360"></p>

## Roadmap

| Stand | Was |
|---|---|
| ✅ | Dual-Screen-EmulationStation, Installer, Rückweg mit einem Tipp |
| ✅ | canvas-ds mit fünf Spielelisten-Ansichten |
| ✅ | Artwork Manager am Gerät – Boxart, Icon, Hero, Icon-Editor, M3U *(ab v12)* |
| ✅ | Kontrollcenter: Schnelleinstellungen, WLAN, Bluetooth, Tastatur, Power-Menü, Spiel beenden, unterer Screen aus |
| ✅ | Gameswitcher – zuletzt gespielte Spiele mit Screenshot vom letzten Stand; **A** weiterspielen, **Y** neu starten *(ab v11)* |
| ✅ | Spielesuche mit **Y** in der Systemansicht, kurze Tour *(ab v12)* |
| 🔜 **als Nächstes** | Kontrollcenter: Seite „Spiel“ – Speicherstände und Tastenkürzel |
| 🔜 | Unterstützung für das normale RG DS |
| 💭 vielleicht | Einstellungsmenü wie am Smartphone, aufgerufen aus dem Kontrollcenter |
| 💭 vielleicht | RetroAchievements – Benachrichtigung und Übersicht |
| 💭 vielleicht | Benutzerprofile mit eigenen Spielständen |
| 🕓 später | Artwork Manager: Spielelisten bearbeiten, M3U in Unterordnern |

## Installation

1. **`rocknix-dualstation-v12.zip`** (enthält canvas-ds) aus dem
   [aktuellen Release](https://github.com/Ninte86hl/rocknix-dualstation/releases/latest) laden.
2. In den Ordner **`ports`** bei den ROMs entpacken (`/storage/roms/ports`).
3. In ES **Ports** → **Install ROCKNIX DualStation** starten.

Der Installer prüft vorher Gerät und ROCKNIX-Version und verändert nichts, wenn sie nicht passen.
Danach stehen unter **Ports** *RGDS Dual-Screen ES*, *RGDS Single-Screen ES* und *Uninstall*.
Ein Update funktioniert genauso.

<details>
<summary>ROMs auf einer ext4-Partition? ZIP über das Netzwerk kopieren</summary>

```bash
scp rocknix-dualstation-v12.zip root@<IP>:/storage/roms/ports/
```
```bash
ssh root@<IP> "cd /storage/roms/ports && unzip rocknix-dualstation-v12.zip && rm rocknix-dualstation-v12.zip"
```
</details>

**Deinstallation:** *Ports → Uninstall ROCKNIX DualStation* stellt das Original-ES samt Theme wieder her.
Spiele, Medien, Spielelisten und Spielstände bleiben unberührt.

## Gut zu wissen

- **Kein ScreenScraper und keine RetroAchievements** in der Dual-Version – die Zugangsdaten
  gibt es nur für den offiziellen ROCKNIX-Build. Zum Scrapen per Ports auf *Single* und zurück.
- PS1: Der Installer stellt **pcsx_rearmed** ein, wenn kein funktionierender Core gewählt ist.
- DS über RetroArch-Cores ist ungetestet; DraStic und DSperate funktionieren.
- Touch in DraStic reagiert nicht? **Follow 3D Renderer** auf *Auto* stellen (auch im Original-ROCKNIX).

Technik, manuelle Installation und wie es funktioniert: [docs/TECHNIK.md](docs/TECHNIK.md)

## Danksagung & Lizenz

Aufgebaut auf der Arbeit der ROCKNIX- und Batocera-Teams, dem ursprünglichen EmulationStation,
canvas-ds von toniremi und dii-ess-aye von beebono. Vollständige Liste: [CREDITS.md](CREDITS.md). Danke! 🙏

Skripte und Dokumentation: MIT ([LICENSE](LICENSE)). Der ES-Patch ändert
[ROCKNIX/emulationstation-next](https://github.com/ROCKNIX/emulationstation-next) (MIT).
Auf Screenshots sichtbare Logos und Grafiken gehören ihren jeweiligen Eigentümern.
