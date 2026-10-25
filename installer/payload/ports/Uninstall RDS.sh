#!/bin/bash
# RDS (RetroDualStation) entfernen und zum Original-ROCKNIX-ES zurueckkehren.
# Die Arbeit macht uninstall.sh ausserhalb von ES.
systemd-run --no-block /bin/bash /storage/rds-install/uninstall.sh
exit 0
