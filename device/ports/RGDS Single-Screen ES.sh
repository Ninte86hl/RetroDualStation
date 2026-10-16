#!/bin/bash
# RGDS Plus: auf das Original-ROCKNIX-ES umschalten
# (Theme art-book-next ueber system-theme, z. B. zum Scrapen mit ScreenScraper).
# Die Arbeit macht es-switch-helper.sh ausserhalb von ES.
systemd-run --no-block /storage/rgds-test/es-switch-helper.sh single
exit 0
