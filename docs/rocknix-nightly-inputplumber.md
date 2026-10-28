# ROCKNIX-Nightly mit InputPlumber – Erkenntnisse (26.10.2026, RG DS Plus)

Getestet: Nightly 20261026 (Branch `next`) auf eigener SD-Karte. Entscheidung: **auf den nächsten stabilen
ROCKNIX-Release warten**, dann mit diesen Erkenntnissen anpassen. Der Umbau liegt als Test auf Branch **`nightly`**
(nicht releasen); Prüf-/Messskripte in `tools/` (rds-nightly-check, rds-inputplumber-check, rds-inputplumber-fix,
rds-sticktest, rds-stickraw, rds-stickcal, rds-stickflick).

## Was sich geändert hat
- **InputPlumber** übernimmt die Tasten: `retrogame_joypad` gibt es nicht mehr. Die Quellgeräte (gpio-keys-control,
  adc-joystick, adc-keys-home) sind versteckt (`/dev/inputplumber/sources/`), das Spiel sieht einen virtuellen
  **DualSense** (uhid, Sysfs `/devices/virtual/misc/uhid/…`) plus „InputPlumber Keyboard“.
- Tastencodes gleich (304/305/307/308/310–318, Anbernic 316, L3 317). **Steuerkreuz = Hat (ABS 16/17)**,
  **L2/R2 nur als Achse 2/5 (0–255), nie als Taste**, Sticks 0–255.
- `start_drastic.sh` beendet gptokeyb selbst (`kill -9`), DSHOOK_WINDOW_SIZE da, DSperate 3.0.5, neues ES,
  CPU bis 1992 MHz. `/etc` ist schreibgeschützt (squashfs).

## ROCKNIX-Fehler (Stand 20261026)
1. **Home-Taste tot:** `capability_maps/anbernic_rgds.yaml` ordnet BTN_BACK `gamepad: button: KeyF1` zu →
   „Invalid or unimplemented button: KeyF1“. Richtig `keyboard: KeyF1` (wie anbernic_gen1/arc). Danach kommt Home
   als KEY_F1 (59) auf „InputPlumber Keyboard“. → Fehlerbericht an ROCKNIX sinnvoll.
2. **Phantom-Stick Plus:** adc-joystick liefert RX/RY (RX = −Y, RY = X) → als rechter Stick weitergegeben. Nur den
   Eintrag aus der Zuordnung zu nehmen reicht nicht; wirksam: `events: exclude: [Gamepad:Axis:RightStick]` am
   adc-joystick in `devices/02-rg-ds-plus.yaml`.
3. **Stick-Kalibrierung:** adc-joystick meldet 15..940, Ruhe X ~300–460 (wandert!), Y ~511, Ausschlag X 77..926,
   Y 105..919. InputPlumber rechnet linear, ohne Mitte/Totzone (nur quadratic_scaling). ES (Schwelle ~70 %) merkt
   wenig, **DraStic (keine Totzone) hielt „links“ dauerhaft**.

## Was im Test funktioniert hat (Branch nightly)
- Startdienst `rds-inputfix` vor InputPlumber: Bind-Mounts der korrigierten yaml-Dateien aus /storage, Stick-Min/Max
  per EVIOCSABS (Werte aus `/storage/.config/rds-stickcal.txt`).
- CC: eingebautes Gamepad = retrogame_joypad oder uhid-DualSense (nach InputPlumber-Neustart neu gefunden), Home =
  F1, L2/R2-Achse ab 50 % als Taste (Anbernic+R2/L2 ✓), eingespeiste Achsen im Gerätebereich, Steuerkreuz als Hat.
- L3-Mikrofon: L3 kam beim Halten mehrfach als Drücken/Loslassen → Loslassen 0,4 s verzögert ✓.
- DraStic-Stick: Stick-Richtungen (Spiel + Menü, controls_a) auf Pfeiltasten, CC gibt den Stick mit Totzone (60/45 %)
  weiter → links zuverlässig; **im DraStic-Menü sprang es beim leichten Tippen noch** (Entprellen/Tastenwiederholung
  ungetestet). Kacheln, Vorspulen, Gameswitcher, Pusten ✓.

## Beim stabilen Release zuerst prüfen
`tools/rds-nightly-check.sh` und `tools/rds-inputplumber-check.sh` laufen lassen: Ist der Home-Fehler behoben? Gibt
es Phantom-Stick-Filter/Totzone von ROCKNIX selbst? Liefert der DualSense L2/R2 als Taste? Dann nur das Nötige aus
Branch `nightly` übernehmen (Commit „InputPlumber-Umbau auf Branch nightly verschoben“ zurücknehmen bzw. einzeln).
Offen: RetroArch + F1 (öffnet RA-Menü?), Grab bei offenem CC (ES über HIDAPI?), Vibration, RG DS (zwei Sticks?).
