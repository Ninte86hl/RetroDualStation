#!/bin/bash
# RGDS Plus: Diagnose, wenn ES nach dem Umschalten nicht mehr reagiert.
# Per SSH ausfuehren: /storage/rgds-test/rgds-diag.sh
# Ergebnis: /storage/rgds-test/diag-<Zeitstempel>.txt

export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock
OUT=/storage/rgds-test/diag-$(date +%Y%m%d-%H%M%S).txt

{
    echo "=== Zeit ==="
    date

    echo; echo "=== essway Status ==="
    systemctl status essway --no-pager 2>&1 | head -15

    echo; echo "=== Drop-in ==="
    ls -l /storage/.config/system.d/essway.service.d/ 2>&1

    echo; echo "=== Umschalt-Log (Ende) ==="
    tail -12 /storage/rgds-test/es-switch.log 2>&1

    echo; echo "=== systemd-run Einheiten ==="
    systemctl list-units --all --no-pager 'run-*' 2>&1 | head -10

    echo; echo "=== ES-Prozesse ==="
    ps 2>/dev/null | grep -i "[e]mulationstation"

    echo; echo "=== Sway Ausgaenge ==="
    swaymsg -t get_outputs -p 2>&1 | grep -E "^Output|Position|Power"

    echo; echo "=== Sway Fenster (app_id, Groesse, Vollbild, Fokus) ==="
    swaymsg -t get_tree 2>/dev/null | python3 -c "
import json,sys
def w(n):
    if n.get('app_id') or n.get('window_properties'):
        print(n.get('app_id') or n.get('name'), n['rect'], 'fs=', n.get('fullscreen_mode'), 'focused=', n.get('focused'), 'visible=', n.get('visible'))
    for c in n.get('nodes', []) + n.get('floating_nodes', []):
        w(c)
w(json.load(sys.stdin))
" 2>&1

    echo; echo "=== Sway Workspaces ==="
    swaymsg -t get_workspaces -p 2>&1

    echo; echo "=== Sway-Config (ES-Zeilen) ==="
    grep -n "rgds\|power" /storage/.config/sway/config 2>&1

    echo; echo "=== Theme ==="
    grep -n "ThemeSet" /storage/.config/emulationstation/es_settings.cfg 2>&1

    echo; echo "=== ES-Log (Ende) ==="
    tail -20 /var/log/es_log.txt 2>&1

    echo; echo "=== Sway-Log (letzte Befehle) ==="
    grep -n "Handling command" /var/log/sway.log 2>/dev/null | tail -20

    echo; echo "=== Journal essway ==="
    journalctl -u essway -n 25 --no-pager 2>&1
} > "$OUT" 2>&1

echo "Diagnose gespeichert: $OUT"
