#!/bin/bash
# RDS (RetroDualStation) – Installer (Ports-Eintrag)
# Die eigentliche Arbeit macht .dualstation/install.sh ausserhalb von ES,
# weil ES waehrend der Installation neu gestartet wird.
DIR="$(cd "$(dirname "$0")" && pwd)"
[ -f "$DIR/.dualstation/install.sh" ] || DIR=/storage/roms/ports
systemd-run --no-block /bin/bash "$DIR/.dualstation/install.sh" "$DIR"
exit 0
