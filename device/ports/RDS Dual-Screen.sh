#!/bin/bash
# RGDS Plus: auf die Dual-Screen-Testversion umschalten
# (Theme dii-ess-aye-rds). Die Arbeit macht es-switch-helper.sh
# ausserhalb von ES, damit der ES-Neustart das Skript nicht abbricht.
systemd-run --no-block /storage/rgds-test/es-switch-helper.sh dual
exit 0
