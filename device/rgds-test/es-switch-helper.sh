#!/bin/bash
# RGDS Plus: zwischen Dual-Screen-Testversion und Original-ES umschalten.
# Aufruf ueber systemd-run (laeuft ausserhalb von essway):
#   systemd-run --no-block /storage/rgds-test/es-switch-helper.sh single|dual
#
# single: Original-ROCKNIX-ES, unterer Screen aus
# dual:   Dual-Screen-ES ueber start-es-dualstation.sh
#
# Theme pro Modus: Beim Umschalten wird das aktuell gewaehlte Theme fuer den
# Modus gespeichert, den man verlaesst, und das zuletzt genutzte Theme des
# Zielmodus wiederhergestellt.
#   /storage/rgds-test/theme.single   (Standard: system-theme)
#   /storage/rgds-test/theme.dual     (Standard: dii-ess-aye-rgds-plus)

MODE="$1"
DROPIN=/storage/.config/system.d/essway.service.d
ESCFG=/storage/.config/emulationstation/es_settings.cfg
SWAYCFG=/storage/.config/sway/config
THEMEDIR=/storage/.config/emulationstation/themes
STATEDIR=/storage/rgds-test
LOG=$STATEDIR/es-switch.log
export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock

log() { echo "$(date) $MODE: $*" >> "$LOG"; }

case "$MODE" in
    single) DEFAULT_THEME="system-theme" ;;
    dual)   DEFAULT_THEME="dii-ess-aye-rgds-plus" ;;
    *)      echo "$(date) Ungueltiger Modus: '$MODE'" >> "$LOG"; exit 1 ;;
esac

if [ "$MODE" = "dual" ] && [ ! -x $STATEDIR/start-es-dualstation.sh ]; then
    log "start-es-dualstation.sh fehlt oder nicht ausfuehrbar, Abbruch"
    exit 1
fi

# Aktueller Modus: Drop-in vorhanden = dual
if [ -f "$DROPIN/rgds.conf" ]; then CURRENT=dual; else CURRENT=single; fi

log "Umschalten gestartet (aktuell: $CURRENT), stoppe essway"
systemctl stop essway

current_theme() {
    sed -n 's|.*<string name="ThemeSet" value="\([^"]*\)" />.*|\1|p' "$ESCFG" 2>/dev/null | head -n 1
}

# Themes koennen in mehreren Ordnern liegen
theme_exists() {
    [ -n "$1" ] || return 1
    for d in "$THEMEDIR" /storage/roms/themes /usr/share/emulationstation/themes; do
        [ -e "$d/$1" ] && return 0
    done
    return 1
}

# --- Theme des verlassenen Modus merken ---
OLD_THEME="$(current_theme)"
if theme_exists "$OLD_THEME"; then
    echo "$OLD_THEME" > "$STATEDIR/theme.$CURRENT"
    log "Theme fuer $CURRENT gemerkt: $OLD_THEME"
fi

# --- Theme des Zielmodus bestimmen ---
THEME="$(cat "$STATEDIR/theme.$MODE" 2>/dev/null)"
if ! theme_exists "$THEME"; then
    [ -n "$THEME" ] && log "gemerktes Theme '$THEME' nicht gefunden, nutze Standard"
    THEME="$DEFAULT_THEME"
fi

# --- Theme setzen (ES ist gestoppt, kann nichts ueberschreiben) ---
if [ -f "$ESCFG" ]; then
    cp "$ESCFG" $STATEDIR/es_settings.last-switch.cfg
    if grep -q 'name="ThemeSet"' "$ESCFG"; then
        sed -i "s|<string name=\"ThemeSet\" value=\"[^\"]*\" />|<string name=\"ThemeSet\" value=\"$THEME\" />|" "$ESCFG"
    elif grep -q '</config>' "$ESCFG"; then
        sed -i "s|</config>|\t<string name=\"ThemeSet\" value=\"$THEME\" />\n</config>|" "$ESCFG"
    else
        log "es_settings.cfg ohne </config>, Theme nicht gesetzt"
    fi
    log "Theme: $(grep 'name="ThemeSet"' "$ESCFG")"
    # Dual: Spielstart ohne Überblendung (schnellerer Wechsel im Gameswitcher)
    if [ "$MODE" = "dual" ]; then
        if grep -q 'name="GameTransitionStyle"' "$ESCFG"; then
            sed -i 's|<string name="GameTransitionStyle" value="[^"]*" />|<string name="GameTransitionStyle" value="instant" />|' "$ESCFG"
        else
            sed -i "s|</config>|\t<string name=\"GameTransitionStyle\" value=\"instant\" />\n</config>|" "$ESCFG"
        fi
    fi
else
    log "es_settings.cfg nicht gefunden, Theme nicht gesetzt"
fi

# --- Schnelle Systemauswahl (links/rechts wechselt das System) ---
# Im Dual-Modus aus, damit links/rechts in Listen-Ansichten nicht ins
# naechste System springen. Der Wert des Single-Modus wird gemerkt und
# beim Zurueckschalten wiederhergestellt. Fehlt der Eintrag, gilt der
# ES-Standard (an).
set_bool() {
    if grep -q "name=\"$1\"" "$ESCFG"; then
        sed -i "s|<bool name=\"$1\" value=\"[^\"]*\" />|<bool name=\"$1\" value=\"$2\" />|" "$ESCFG"
    elif grep -q '</config>' "$ESCFG"; then
        sed -i "s|</config>|\t<bool name=\"$1\" value=\"$2\" />\n</config>|" "$ESCFG"
    fi
}
if [ -f "$ESCFG" ]; then
    QSS="$(sed -n 's|.*<bool name="QuickSystemSelect" value="\([^"]*\)" />.*|\1|p' "$ESCFG" | head -n 1)"
    [ -n "$QSS" ] || QSS=true
    if [ "$MODE" = "dual" ]; then
        [ "$CURRENT" = "single" ] && echo "$QSS" > "$STATEDIR/quicksystemselect.single"
        set_bool QuickSystemSelect false
        log "Schnelle Systemauswahl aus (Single-Wert gemerkt: $(cat "$STATEDIR/quicksystemselect.single" 2>/dev/null))"
    else
        RESTORE="$(cat "$STATEDIR/quicksystemselect.single" 2>/dev/null)"
        [ -n "$RESTORE" ] || RESTORE=true
        set_bool QuickSystemSelect "$RESTORE"
        log "Schnelle Systemauswahl wiederhergestellt: $RESTORE"
    fi
fi

# --- Drop-in und Sway-Config ---
if [ "$MODE" = "dual" ]; then
    mkdir -p "$DROPIN"
    printf '[Service]\nExecStart=\nExecStart=%s/start-es-dualstation.sh\n' "$STATEDIR" > "$DROPIN/rgds.conf"
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
