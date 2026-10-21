# Theming for RetroDualStation

ES runs as one window across both screens. Theme positions are relative to that window
(0 … 1), so on the RG DS Plus (2048 × 768) the left half is the **top** screen and the right half
the **bottom** screen.

To stay independent of a specific device, use the screen variables (ES patch 005):

| Variable | Meaning |
|---|---|
| `${screen.dual}` | `true` on a dual-screen device |
| `${screen.menu}` | `top` or `bottom` – where ES shows menus |
| `${screen.top.relx}`, `${screen.top.rely}` | top screen position, relative to the window (0 … 1) |
| `${screen.top.relwidth}`, `${screen.top.relheight}` | top screen size, relative |
| `${screen.top.x}`, `.y`, `.width`, `.height` | the same in pixels |
| `${screen.bottom.…}` | the same for the bottom screen |

Example – a hero image filling the top screen:

```xml
<image name="hero">
  <pos>${screen.top.relx} ${screen.top.rely}</pos>
  <size>${screen.top.relwidth} ${screen.top.relheight}</size>
  <path>{game:image}</path>
</image>
```

The values come from `/storage/.config/retrodualstation/screens.cfg` (see
[BILDSCHIRME.md](BILDSCHIRME.md)); without it the RG DS Plus layout is used.
Artwork names: [ARTWORK.md](ARTWORK.md).
