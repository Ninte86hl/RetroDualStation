# advanced_drastic mit RDS (Test)

[advanced_drastic](https://github.com/trngaje/advanced_drastic) von trngaje – **nicht von RDS mitgeliefert** (keine Lizenz).
Selbst installiert läuft es mit RDS (Test 26.10.2026, RG DS Plus): Beenden über Home/CC (Quit-Taste F7), automatischer
Speicherpunkt, Auto-Laden, Kachel „Tauschen“, Kürzel, Mikrofon (CC hört ab, L3).

- **RG DS Plus:** offiziell nicht unterstützt – `rds-plus-layout.sh` legt das fehlende Layout an.
- ES *Microphone sensitivity* (NDS) auf **off** – sonst stürzt der Starter ab (libdrastouch im Shell-Starter).
- In advanced_drastic **Enable Device Microphone = no**, **Enable auto savestate = no** (RDS macht Platz 0).
- **Zurück zum ROCKNIX-DraStic:** `rds-adv-zurueck.sh` (geführt): entfernt nur, was advanced_drastic dazugelegt hat, holt
  den Starter aus der Sicherung des Installskripts (`/storage/.config/drastic.tar.gz`) und lässt drastic.cfg, Spielstände,
  BIOS und das RDS-Pust-Geräusch stehen – trngajes uninstall-Skript würde den Ordner auf den Installationstag zurücksetzen.
