# Konzept: Bildschirm-Bereiche in ES

Stand: 20.10.2026 · Anlass: [Issue #5](https://github.com/Ninte86hl/RetroDualStation/issues/5) · Noch kein Code.

## Ausgangslage

- ES läuft als **ein** Fenster über beide Ausgaben (Sway: globales Vollbild, 2048 × 768).
- Patch 001 setzt Menüs, Meldungen und Tastatur auf einen Bildschirm – über eine **feste Abfrage**
  „Fenster ist 2048 × 768 → Breite 1024“ (`RGDS_MENU_W` und gleichwertige Zeilen, rund 110 Stellen).
- Themes (canvas-ds) rechnen mit dem ganzen Fenster; „oben“/„unten“ steckt in festen Koordinaten.

Folge: Alles hängt an zwei gleich großen 1024 × 768-Bildschirmen. Normales RG DS (2 × 640 × 480),
Thor oder RG DDS (ungleiche Größen) gehen so nicht.

## Ziel

ES kennt die Bildschirme als **eigene Bereiche** (Position, Größe). Menüs und Themes beziehen sich
auf einen Bereich statt auf feste Zahlen. Ein neues Gerät = eine neue Konfiguration, kein neuer Patch.

## Stufe A – Bereiche zentral (kleiner Umbau, gleiches Verhalten) – umgesetzt: Patch 004

- Neu in es-core: `RdsScreens` mit `top()`, `bottom()`, `menu()` → jeweils Rechteck (x, y, b, h).
- Quelle: `/storage/.config/retrodualstation/screens.cfg`, z. B.
  ```
  # RG DS Plus (Fenster: links = oben, rechts = unten)
  top=0,0,1024,768
  bottom=1024,0,1024,768
  menu=top
  ```
  Fehlt die Datei: aus der Fenstergröße ableiten (2048 × 768 → zwei Hälften, wie heute;
  sonst ein Bildschirm = ganzes Fenster → Verhalten wie Original-ES).
- Alle ~110 festen Stellen aus Patch 001 lesen `RdsScreens::menu()` statt `2048/768/1024`.
  Dabei wird auch die **Position** des Menübereichs berücksichtigt (heute nur die Breite).
- Der Installer schreibt `screens.cfg` passend zum erkannten Gerät.
- Test: RG DS Plus muss sich exakt wie v12 verhalten.
- Stand Patch 004: Breiten und X-Positionen kommen aus den Bereichen; Höhen/Y nutzen noch die
  Fensterhöhe (reicht für gleich hohe Bildschirme, z. B. RG DS). Der Installer legt `screens.cfg` an (ab v13), vorhandene bleibt.

## Stufe B – Themes bekommen die Bereiche – Variablen umgesetzt: Patch 005 ([THEMES.md](THEMES.md))

- Neue Theme-Variablen (ES kennt schon `${screen.width}`/`${screen.height}`):
  `${screen.top.x}`, `${screen.top.y}`, `${screen.top.width}`, `${screen.top.height}`,
  dasselbe für `bottom`. Damit kann ein Theme ohne feste Zahlen rechnen.
- Optional, später: Eigenschaft `<screen>top</screen>` je Element – `pos`/`size` gelten dann relativ
  zum Bereich (0…1 innerhalb des Bildschirms). Komfortabler für Theme-Bauer, aber tieferer Eingriff
  in `GuiComponent::applyTheme`; erst wenn Stufe B mit Variablen läuft.
- Alte Themes bleiben unverändert lauffähig.

## Stufe C – canvas-ds und Geräte

**Ergebnis der Prüfung (20.10.2026):** canvas-ds rechnet mit relativen Koordinaten (0 … 1 des Fensters).
Bei zwei **gleich großen 4:3-Bildschirmen nebeneinander** – RG DS Plus (2 × 1024 × 768) wie normales RG DS
(2 × 640 × 480) – passt das Overlay also schon ohne Änderung. Ein Umbau auf die Variablen lohnt sich erst
für Geräte mit ungleichen Bildschirmen und wird bis dahin zurückgestellt (weniger Eingriff in toniremis Theme).


- canvas-ds-Overlay auf die neuen Variablen umstellen (statt fester 1024er-Koordinaten).
- Geräteprofile: RG DS Plus (2 × 1024 × 768), RG DS (2 × 640 × 480), weitere bei Bedarf
  (ungleiche Größen: Fenster = umschließendes Rechteck, ungenutzte Flächen bleiben schwarz).
- Kontrollcenter liest dieselbe `screens.cfg` (Ausgaben/Größen statt fester Werte); Theme-Optionen
  für das CC später.

## Reihenfolge und Risiko

| Stufe | Aufwand | Risiko | Nutzen |
|---|---|---|---|
| A | mittel (viele, aber gleichförmige Stellen) | gering – Verhalten bleibt gleich | Grundlage für RG DS |
| B (Variablen) | klein | gering | Themes unabhängig von festen Zahlen |
| B (`<screen>`) | groß | mittel | bequemer für Theme-Bauer |
| C | mittel | gering | normales RG DS, weitere Geräte |

Vorschlag: A → B (Variablen) → C mit dem normalen RG DS als erstem neuen Gerät.
`<screen>`-Eigenschaft nur, wenn Theme-Bauer danach fragen.
