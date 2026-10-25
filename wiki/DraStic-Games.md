🇩🇪 [Deutsch](DraStic-Spiele)

# DraStic: games that swap screens

Some DS games swap top and bottom screen now and then – e.g. the shop in *Zelda: Phantom Hourglass*. With
**Threaded 3D = On** (ROCKNIX default) DraStic gets this wrong in some games: the picture ends up on the wrong screen and
touch stays where it was.

**Fix per game:** select the game in ES → **advanced game settings** → **Threaded 3D = Off**. DraStic then follows the swap
by itself, touch included. Only this game is affected; all others keep Threaded 3D.

**Fallback:** **L3** or the **Swap** tile in the [Control Center](Control-Center) swaps the screens by hand.

## List

| Game | Needs Threaded 3D off | Status |
|---|---|---|
| The Legend of Zelda: Phantom Hourglass | yes (shop, items) | tested with RDS, RG DS + RG DS Plus |
| The Legend of Zelda: Spirit Tracks | yes (same engine) | reported, not yet tested with RDS |
| Metroid (as reported, probably *Prime Hunters*) | yes | reported¹ |
| Dragon Quest IV | yes | reported¹ |
| The Rub Rabbits! | yes | reported¹ |
| Mario Kart DS | no – works correctly with Threaded 3D | reported¹ |

¹ from [GammaOSNext issue #225](https://github.com/TheGammaSqueeze/GammaOSNext/issues/225) (reports by
[WGB-works](https://github.com/WGB-works) and others) – also DraStic on the RG DS.

If a game stutters without Threaded 3D, keep it on and use **L3** when needed.

**Found more games?** Please report them as an [issue](https://github.com/Ninte86hl/RetroDualStation/issues) – game name
and whether Threaded 3D off helps. Every report is credited in the [credits](https://github.com/Ninte86hl/RetroDualStation/blob/main/CREDITS.md).
