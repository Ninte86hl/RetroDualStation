🇩🇪 [Deutsch](Gut-zu-wissen)

- **RG DS: larger text in ES menus** – a deliberate usability choice: on the smaller 640 × 480 screens ES shows menu text a bit larger than true to scale. Fewer entries fit at once (e.g. scroll to *System settings* and *Quit*), but everything stays easy to read. Control Center, Game switcher and Power menu scale with the screen.
- **RetroAchievements:** *Main menu → RetroAchievements* opens the settings; progress and achievements are on page 3 of the [Control Center](Control-Center) – also for DS games in DSperate, not in DraStic ([more](RetroAchievements)).
- **PS1:** the installer sets **pcsx_rearmed** if no working core is selected.
- **DS:** DraStic and DSperate work; RetroArch DS cores are untested.
- **DraStic touch not responding?** With **Follow 3D Renderer = On** the touch picture may be on top – on the RG DS just tap on top (its top screen has touch too), on the RG DS Plus set *Follow 3D* to *Auto* (also happens on stock ROCKNIX).
- **DraStic: microphone** – blow like on a DS (the Control Center listens; normal talking does not trigger, shouting does – like on a real DS), or hold **L3**. Please leave ES's *Microphone sensitivity* (ROCKNIX detection) *off* – RDS does not need it, and with advanced_drastic it prevents the start.
- **DraStic: picture or touch on the wrong screen?** Some games swap top and bottom (e.g. the shop in *Zelda: Phantom Hourglass*). With **Threaded 3D = Off** for that game (select the game → advanced game settings) DraStic follows the swap correctly, touch included. Otherwise use the **Swap** tile in the [Control Center](Control-Center). Known games: [DraStic games](DraStic-Games).
- **Back to stock:** *Ports → RDS Single-Screen*; *Uninstall* restores stock ES, theme and your original settings and removes everything from RDS – games, artwork, game lists, save states and saves stay untouched. A safety copy of your original settings is kept in `roms/backup` until the uninstall has finished.

Which files RDS creates: [RDS files](Files)

Technical details and manual installation: [TECHNICAL.md](https://github.com/Ninte86hl/RetroDualStation/blob/main/docs/TECHNICAL.md)
