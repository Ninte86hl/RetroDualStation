#!/bin/bash
# ROCKNIX DualStation – canvas-ds-Theme installieren (Ports-Eintrag)
# Die Arbeit macht .canvas-ds/install-canvas.sh ausserhalb von ES.
DIR="$(cd "$(dirname "$0")" && pwd)"
[ -f "$DIR/.canvas-ds/install-canvas.sh" ] || DIR=/storage/roms/ports
systemd-run --no-block /bin/bash "$DIR/.canvas-ds/install-canvas.sh" "$DIR"
exit 0
