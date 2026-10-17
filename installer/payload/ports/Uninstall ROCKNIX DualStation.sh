#!/bin/bash
# ROCKNIX DualStation entfernen und zum Original-ROCKNIX-ES zurueckkehren.
# Die Arbeit macht uninstall.sh ausserhalb von ES.
systemd-run --no-block /bin/bash /storage/rgds-test/uninstall.sh
exit 0
