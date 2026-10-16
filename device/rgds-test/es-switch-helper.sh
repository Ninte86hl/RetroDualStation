#!/bin/bash
# RGDS Plus: zwischen Dual-Screen-Testversion und Original-ES umschalten.
# Aufruf ueber systemd-run (laeuft ausserhalb von essway):
#   systemd-run --no-block /storage/rgds-test/es-switch-helper.sh single|dual
#
# single: Original-ROCKNIX-ES, Theme system-theme (art-book-next), unterer Screen aus
# dual:   Testversion ueber start-es-v2-diag.sh, Theme dii-ess-aye-rgds-plus

MODE="$1"
DROPIN=/storage/.config/system.d/essway.service.d
ESCFG=/storage/.config/emulationstation/es_settings.cfg
SWAYCFG=/storage/.config/sway/config
LOG=/storage/rgds-test/es-switch.log
export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock

log() { echo "$(date) $MODE: $*" >> "$LOG"; }

case "$MODE" in
    single) THEME="system-theme" ;;
    dual)   THEME="dii-ess-aye-rgds-plus" ;;
    *)      echo "$(date) Ungueltiger Modus: '$MODE'" >> "$LOG"; exit 1 ;;
esac

if [ "$MODE" = "dual" ] && [ ! -x /storage/rgds-test/start-es-v2-diag.sh ]; then
    log "start-es-v2-diag.sh fehlt oder nicht ausfuehrbar, Abbruch"
    exit 1
fi

log "Umschalten gestartet, stoppe essway"
systemctl stop essway

# --- Theme setzen (ES ist gestoppt, kann nichts ueberschreiben) ---
if [ -f "$ESCFG" ]; then
    cp "$ESCFG" /storage/rgds-test/es_settings.last-switch.cfg
    if grep -q 'name="ThemeSet"' "$ESCFG"; then
        sed -i "s|<string name=\"ThemeSet\" value=\"[^\"]*\" />|<string name=\"ThemeSet\" value=\"$THEME\" />|" "$ESCFG"
    elif grep -q '</config>' "$ESCFG"; then
        sed -i "s|</config>|\t<string name=\"ThemeSet\" value=\"$THEME\" />\n</config>|" "$ESCFG"
    else
        log "es_settings.cfg ohne </config>, Theme nicht gesetzt"
    fi
    log "Theme: $(grep 'name="ThemeSet"' "$ESCFG")"
else
    log "es_settings.cfg nicht gefunden, Theme nicht gesetzt"
fi

# --- Drop-in und Sway-Config ---
if [ "$MODE" = "dual" ]; then
    mkdir -p "$DROPIN"
    printf '[Service]\nExecStart=\nExecStart=/storage/rgds-test/start-es-v2-diag.sh\n' > "$DROPIN/rgds.conf"
    # Sway-Anpassung erledigt rgds-sway-fix.sh beim Start
else
    rm -f "$DROPIN/rgds.conf"
    rmdir "$DROPIN" 2>/dev/null
    # Nur die ES-Zeile zuruecksetzen, nicht die DraStic-/Secondary-Regeln
    if [ -f "$SWAYCFG" ]; then
        sed -i 's/focus output DSI-2, output DSI-1 power on/focus output DSI-2, output DSI-1 power off/' "$SWAYCFG"
    fi
fi

systemctl daemon-reload
log "Starte essway"
systemctl start essway
log "fertig"
exit 0
