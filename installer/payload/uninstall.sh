#!/bin/bash
# ROCKNIX DualStation – Deinstallation
# Aufruf: systemd-run --no-block /bin/bash /storage/rgds-test/uninstall.sh
# Schaltet auf das Original-ROCKNIX-ES zurueck und entfernt alle Dateien
# von ROCKNIX DualStation. Spiele, Medien und Gamelists bleiben unberuehrt.

DEST=/storage/rgds-test
PORTS=/storage/roms/ports
THEMEDIR=/storage/.config/emulationstation/themes
LOG=/storage/dualstation-uninstall.log

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

log "=== Deinstallation ROCKNIX DualStation $(cat $DEST/VERSION 2>/dev/null) ==="

# Ports-Eintraege vor dem ES-Neustart entfernen, damit ES sie nicht mehr anzeigt
for f in "RGDS Dual-Screen ES.sh" "RGDS Single-Screen ES.sh" "Uninstall ROCKNIX DualStation.sh"; do
    rm -f "$PORTS/$f" && log "entfernt: $PORTS/$f"
done

# Zurueck auf Single (Original-ES, Original-Theme, Drop-in weg, Sway zurueck)
if [ -x "$DEST/es-switch-helper.sh" ]; then
    /bin/bash "$DEST/es-switch-helper.sh" single
    log "auf Single umgeschaltet"
else
    rm -f /storage/.config/system.d/essway.service.d/rgds.conf
    rmdir /storage/.config/system.d/essway.service.d 2>/dev/null
    systemctl daemon-reload
    systemctl restart essway
    log "Helper fehlte, Drop-in direkt entfernt"
fi

# Kontrollcenter und Geräteeinstellungen
SYSD=/storage/.config/system.d
systemctl stop rds-controlcenter 2>/dev/null
rm -f "$SYSD/essway.service.wants/rds-controlcenter.service" "$SYSD/rds-controlcenter.service" \
      "$SYSD"/*.target.wants/rds-resume.service "$SYSD/rds-resume.service" \
      /storage/.config/logind.conf.d/rds-logind-powerkey.conf
rm -rf /storage/.config/retrodualstation /storage/.config/rds-controlcenter
systemctl daemon-reload
systemctl kill -s HUP systemd-logind 2>/dev/null
. /etc/profile 2>/dev/null
set_setting rocknix.bottomscreen.type "$(cat "$DEST/bottomscreen.before" 2>/dev/null || echo vc)" 2>/dev/null
sed -i '/RetroDualStation: gptokeyb/d; /4660:22136:Fake_Keyboard/d' /storage/.config/sway/config 2>/dev/null
sed -i '/^# RetroDualStation$/,/^invisible=1$/d' /storage/.config/mako/config 2>/dev/null
log "Kontrollcenter und Geraeteeinstellungen entfernt"

rm -rf "$THEMEDIR/dii-ess-aye-rgds-plus" && log "entfernt: Theme dii-ess-aye-rgds-plus"
if [ -d "$THEMEDIR/canvas-ds-rgds-plus" ]; then
    rm -rf "$THEMEDIR/canvas-ds-rgds-plus" /storage/.config/emulationstation/themesettings/canvas-ds-rgds-plus.cfg
    log "entfernt: Theme canvas-ds-rgds-plus"
fi
rm -f /storage/dualstation-canvas-install.log
rm -rf "$DEST" && log "entfernt: $DEST"
rm -f /storage/dualstation-install.log && log "entfernt: /storage/dualstation-install.log"

log "=== Deinstallation fertig ==="
exit 0
