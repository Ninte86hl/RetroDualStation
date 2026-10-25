#!/bin/sh
# RGDS Plus Dual-Screen: Sway-Config vor dem ES-Start anpassen.
# Hintergrund: /usr/lib/autostart/common/111-sway-init schreibt
# /storage/.config/sway/config bei jedem Boot neu.
# Aufruf aus /storage/rds-install/start-es-dualstation.sh vor dem exec.

CFG=/storage/.config/sway/config
export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock

[ -f "$CFG" ] || exit 0

# 1. Testversion global ueber beide Screens (nach der DP-1-Regel einfuegen)
if ! grep -q 'emulationstation-rgds' "$CFG"; then
    sed -i '/for_window \[app_id="emulationstation"\] move output DP-1/a for_window [app_id="^emulationstation-rgds"] fullscreen enable global' "$CFG"
fi
# Fallback, falls die DP-1-Regel fehlt
if ! grep -q 'emulationstation-rgds' "$CFG"; then
    echo 'for_window [app_id="^emulationstation-rgds"] fullscreen enable global' >> "$CFG"
fi

# 2. Unteren Screen bei Reload nicht mehr ausschalten
sed -i 's/output DSI-1 power off/output DSI-1 power on/' "$CFG"

# 3. Sway neu laden, damit die Regeln sofort gelten
swaymsg reload >/dev/null 2>&1

exit 0
