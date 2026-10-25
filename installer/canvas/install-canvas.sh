#!/bin/bash
# ROCKNIX DualStation – canvas-ds (RG DS Plus) installieren
# Kopiert das Theme nach /storage/.config/emulationstation/themes,
# entfernt die Installer-Dateien und startet ES neu.

PORTS="${1:-/storage/roms/ports}"
SRC="$PORTS/.canvas-ds"
THEMEDIR=/storage/.config/emulationstation/themes
NAME=canvas-rds
LOG=/storage/dualstation-canvas-install.log

log()    { echo "$(date '+%F %T') $*" >> "$LOG"; }
notify() { curl -s -m 3 -X POST -H 'Content-Type: text/plain' --data "$1" http://127.0.0.1:1234/notify >/dev/null 2>&1; }
msgbox() { curl -s -m 3 -X POST -H 'Content-Type: text/plain' --data "$1" http://127.0.0.1:1234/messagebox >/dev/null 2>&1; }
fail()   { log "ABBRUCH: $1"; msgbox "canvas-ds: $1 Nothing was changed. Log: $LOG"; exit 1; }

log "=== Installation canvas-ds ($(cat "$SRC/VERSION" 2>/dev/null)) ==="

[ -f "$SRC/$NAME/theme.xml" ] || fail "Installer files are incomplete (.canvas-ds folder missing?)."
[ -x /storage/rds-install/es-switch-helper.sh ] || [ -x /storage/rgds-test/es-switch-helper.sh ] || fail "Please install ROCKNIX DualStation first – this theme needs the dual-screen EmulationStation."

notify "Installing the canvas-ds theme – EmulationStation will restart in a moment..."
sleep 2

mkdir -p "$THEMEDIR"
rm -rf "$THEMEDIR/$NAME.new"
# Verschieben statt kopieren (spart Platz und Zeit; ueber Dateisystemgrenzen kopiert mv)
mv "$SRC/$NAME" "$THEMEDIR/$NAME.new" || { rm -rf "$THEMEDIR/$NAME.new"; fail "Could not copy the theme (not enough space?)."; }
rm -rf "$THEMEDIR/$NAME"
mv "$THEMEDIR/$NAME.new" "$THEMEDIR/$NAME"
log "Theme kopiert: $THEMEDIR/$NAME"

rm -f "$PORTS/Install canvas-ds theme.sh"
rm -rf "$SRC"
log "Installer-Dateien entfernt"

systemctl restart essway
log "ES neu gestartet"

# Hinweis anzeigen, sobald ES wieder antwortet
for i in $(seq 1 60); do
    sleep 2
    curl -s -m 2 http://127.0.0.1:1234/ >/dev/null 2>&1 && break
done
sleep 3
msgbox "canvas-ds is installed. Select it under USER INTERFACE SETTINGS > THEME SET. The Ports switch remembers it for the dual-screen mode."
log "=== fertig ==="
exit 0
