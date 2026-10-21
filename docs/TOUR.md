# RetroDualStation – Quick tour

*[Deutsche Fassung](TOUR.de.md)*

RetroDualStation turns ROCKNIX on the Anbernic RG DS Plus into **one system with two screens**.
This tour shows the additions on top of EmulationStation: the two special buttons, the
Control Center, the Game switcher, the Power menu and the Artwork Manager.

The same tour runs once on the device after installation. You can start it again at any time
from the Control Center with **Select**.

---

## 0. Your entries in Ports

After installing, you'll find RDS in **Ports** by these icons:

| | Entry | What for |
|:-:|---|---|
| <img src="icons/rds-install.png" width="48"> | **Install RDS** | Installs or updates RDS |
| <img src="icons/rds-dual.png" width="48"> | **RDS Dual-Screen** | ES across both screens |
| <img src="icons/rds-single.png" width="48"> | **RDS Single-Screen** | Stock ES on one screen, e.g. for scraping |
| <img src="icons/rds-artwork.png" width="48"> | **Artwork Manager** | Boxart, icons and hero images on the device |
| <img src="icons/rds-uninstall.png" width="48"> | **Uninstall RDS** | Back to stock; games and saves stay |

---

## 1. The two special buttons

<p align="center"><img src="tour/geraet-tasten-en.png" alt="Anbernic button and Home button on the RG DS Plus" width="560"></p>

| Button | Press | Action |
|---|---|---|
| **Anbernic** | short | Open / close the **Control Center** |
| **Home** | short | In a game: **save** and return to EmulationStation |
| **Home** | long (1.5 s) | Open the **Game switcher** |
| **Home** | twice | In a game: jump to the **previous game** (in ES: Game switcher) |
| **Power** | short | Open the **Power menu** |
| **Power** | long (0.8 s) | **Sleep** immediately |

---

## 2. Control Center

<p align="center"><img src="tour/tour-kontrollcenter.png" alt="Control Center" width="480"></p>

Open it with the **Anbernic** button – in EmulationStation and in every game (the game pauses).

- **Now playing:** the running game with *Quit game*.
- **Brightness** of the top and bottom screen and **volume** – with the D-pad or by touch.
- **Performance:** Battery saver · Balanced · Performance.
- **Tiles:** Wi-Fi and Bluetooth (**X / Y** – details and pairing), *Bottom screen off*
  (wake it with the Anbernic button) and *Sleep*.
- Top right: power menu, light/dark theme and accent colour.

**L1 / R1** – switch page · **B** – close · **Select** – start this tour again

### Game page

| | |
|---|---|
| <img src="tour/tour-spiel.png" alt="Game page"> | <img src="tour/tour-slots.png" alt="Save slots"> |

In a game, press **R1** for the game page (RetroArch, DSperate and DraStic):
- **Save / Load** open slots 0–8 with preview picture and time. Loading preselects the newest one.
  The **bin** (or **X**, **X**) deletes a save.
- Icons: **Emulator menu · Restart · Fast forward · Slow motion · Screenshot · Buttons · Quit**.
- **Buttons** shows the original system's buttons (e.g. NES: D-pad, A, B, Select, Start) and the emulator's shortcuts.
- After an action the Control Center closes and you're back in the game.

### Shortcuts – the same in every emulator

<p align="center"><img src="tour/tour-tasten.png" alt="Button layout" width="480"></p>

**Hold the Anbernic button** and press a second button. Everything also works with a tap in the Control Center.

| Anbernic + | Action |
|---|---|
| **R1** | Fast forward on/off |
| **R2 / L2** | Save / Load |
| **X** | Emulator menu |
| **Y** | Show FPS |
| **Start** | Quit game |
| **◀ / ▶** | Save slot − / + |

DraStic has no button combinations: save and load are on R2 and L2, menu and fast forward via the Control Center.

### RetroAchievements (page 3)

| | |
|---|---|
| <img src="tour/tour-ra.png" alt="RetroAchievements"> | <img src="tour/tour-toast.png" alt="Achievement unlocked"> |

Your account, your progress in the running game and all achievements – **A** opens one with description,
points and rarity. A new achievement briefly appears **on top of the game**, and so does the **volume** on Vol+ / Vol−.
Sign in in ES: *Game settings → RetroAchievements settings*. Supported: RetroArch games.

---

## 3. Game switcher

<p align="center"><img src="tour/tour-gameswitcher.png" alt="Game switcher" width="480"></p>

Hold **Home** for 1.5 seconds. In a game, **Home twice** jumps straight to the previous game. Your recently played games appear as cards with their last screen.
Switching saves the running game automatically and continues the next one where you left off.

**◀ ▶** – choose · **A** – Resume · **Y** – Restart · **X** – Remove from list · **B** – Close

---

## 4. Power menu

<p align="center"><img src="tour/tour-powermenue.png" alt="Power menu" width="480"></p>

Press **Power** briefly: *Sleep*, *Restart*, *Power off* and *Restart ES*.
Holding Power sends the device to sleep right away.

**▲ ▼** – choose · **A** – confirm · **X** – details · **B** – cancel

---

## 5. Artwork Manager

| | |
|---|---|
| <img src="tour/tour-artwork-liste.png" alt="Game list with filter"> | <img src="tour/tour-artwork-settings.png" alt="Settings"> |
| <img src="tour/tour-artwork-spiel.png" alt="Game view with mix preview"> | <img src="tour/tour-artwork-editor.png" alt="Icon editor"> |

Start it from **Ports → Artwork Manager**. It adds **Boxart**, **Cartridge** (1:1 icon) and
**Image** (hero) to your games – the top screen shows how the three look together.

**Requirement:** every system needs a `gamelist.xml`. Create it once with the scraper in
single-screen mode (original ROCKNIX interface); RetroDualStation uses the same list.

| Where | Button | Action |
|---|---|---|
| System list | **Start** | Single search: edit one game |
| | **Select** | Batch search: all games with missing artwork, one after another |
| | **Y** | Search a game across all systems |
| | **X** | Settings (API key, backups, merge multi-disc games as M3U, cache, quick guide) |
| Game list | **X** | Open the icon editor for this game directly |
| | **Y** | Filter: all · missing · no artwork |
| Game view | **◀ ▶** | Choose image |
| | **L / R** | Artwork style |
| | **A** | Take image |
| | **Start** | Save |
| | **Y** | Search another game |
| | **L3** | Refresh the artwork search |
| | **R3** | Mix view / large view on top |
| | **X** | Icon editor: turn the chosen icon into a 1:1 image with iiSU border (◀ ▶ ▲ ▼ move · L / R zoom · Y border). Not needed – and greyed out – for icons that already have the iiSU border |

Before the first save per system a backup is created (can be turned off in the settings).
**Own images:** put PNG/JPG/WebP files into `ports/artworkmanager/eigene/` (or `eigene/<system>/`), named like the game – they appear first in every tab marked *Own image*. Everything in `eigene/alle/` appears for every game.

The SteamGridDB API key can also be entered on a PC in
`/storage/roms/ports/artworkmanager/settings.cfg`.

---

*Logos and artwork in screenshots belong to their respective owners.*
