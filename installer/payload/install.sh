#!/bin/bash
# ROCKNIX DualStation – Installation
# Aufruf: systemd-run --no-block /bin/bash <ports>/.dualstation/install.sh <ports>
#
# 1. Pruefen: RG DS Plus (DSI-1 + DSI-2 mit 1024x768), ES-Binary laeuft auf
#    dieser ROCKNIX-Version (keine fehlenden Bibliotheken)
# 2. Dateien nach /storage/rgds-test, Theme, Ports-Eintraege kopieren
# 3. Installer-Dateien entfernen und auf Dual umschalten

PORTS="${1:-/storage/roms/ports}"
SRC="$PORTS/.dualstation"
DEST=/storage/rgds-test
THEMEDIR=/storage/.config/emulationstation/themes
ESCFG=/storage/.config/emulationstation/es_settings.cfg
LOG=/storage/dualstation-install.log
export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock

VERSION="$(cat "$SRC/VERSION" 2>/dev/null)"
BIN="$(cd "$SRC" && ls emulationstation-rgds-* 2>/dev/null | head -n 1)"

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

# Meldung in ES anzeigen (ES-HTTP-Schnittstelle, Port 1234)
notify()  { curl -s -m 3 -X POST -H 'Content-Type: text/plain' --data "$1" http://127.0.0.1:1234/notify >/dev/null 2>&1; }
msgbox()  { curl -s -m 3 -X POST -H 'Content-Type: text/plain' --data "$1" http://127.0.0.1:1234/messagebox >/dev/null 2>&1; }

fail() {
    log "ABBRUCH: $1"
    msgbox "ROCKNIX DualStation: $1 Nothing was changed. Log: $LOG"
    exit 1
}

log "=== Installation ROCKNIX DualStation $VERSION ==="
log "Quelle: $SRC"
grep -E '^(NAME|VERSION|VERSION_ID|BUILD_ID)=' /etc/os-release 2>/dev/null | while read -r l; do log "os-release: $l"; done

# --- 1. Pruefungen (ES laeuft noch, Meldungen sind sichtbar) ---
[ -n "$BIN" ] && [ -f "$SRC/$BIN" ] || fail "Installer files are incomplete (.dualstation folder missing?)."

OUTPUTS="$(swaymsg -t get_outputs -r 2>/dev/null)"
if ! printf '%s' "$OUTPUTS" | python3 -c '
import json, sys
o = {x["name"]: x for x in json.load(sys.stdin)}
ok = all(n in o and any(m["width"] == 1024 and m["height"] == 768 for m in o[n].get("modes", [])) for n in ("DSI-1", "DSI-2"))
sys.exit(0 if ok else 1)' 2>>"$LOG"; then
    log "Ausgaenge: $(printf '%s' "$OUTPUTS" | tr -d '\n' | head -c 600)"
    fail "This version only supports the Anbernic RG DS Plus (two 1024x768 screens)."
fi
log "Geraet: RG DS Plus erkannt"

chmod +x "$SRC/$BIN" 2>/dev/null
cp "$SRC/$BIN" /tmp/dualstation-bincheck && chmod +x /tmp/dualstation-bincheck
MISSING="$(ldd /tmp/dualstation-bincheck 2>&1 | grep 'not found')"
rm -f /tmp/dualstation-bincheck
if [ -n "$MISSING" ]; then
    log "Fehlende Bibliotheken: $MISSING"
    fail "The included EmulationStation does not match this ROCKNIX version."
fi
log "ES-Binary: $BIN, Bibliotheken ok"

notify "Installing ROCKNIX DualStation – EmulationStation will restart in a moment..."
sleep 2

# --- 2. Dateien kopieren ---
mkdir -p "$DEST" || fail "Could not create $DEST."

if [ -f "$ESCFG" ] && [ ! -f "$DEST/es_settings.before-install.cfg" ]; then
    cp "$ESCFG" "$DEST/es_settings.before-install.cfg"
    log "Sicherung: $DEST/es_settings.before-install.cfg"
fi

# Binary ueber Zwischennamen, damit ein laufendes ES nicht stoert
cp "$SRC/$BIN" "$DEST/.$BIN.new" && chmod +x "$DEST/.$BIN.new" && mv -f "$DEST/.$BIN.new" "$DEST/$BIN" \
    || fail "Could not copy $BIN."
# Aeltere Versionen entfernen
for old in "$DEST"/emulationstation-rgds-*; do
    [ "$(basename "$old")" = "$BIN" ] && continue
    [ -f "$old" ] && rm -f "$old" && log "entfernt: $old"
done

for f in start-es-v2-diag.sh rgds-sway-fix.sh es-switch-helper.sh rgds-diag.sh uninstall.sh; do
    cp "$SRC/rgds-test/$f" "$DEST/$f" || fail "Could not copy $f."
    chmod +x "$DEST/$f"
done
# Startskript auf das mitgelieferte Binary zeigen lassen
sed -i "s|/storage/rgds-test/emulationstation-rgds-[^ ]*|/storage/rgds-test/$BIN|" "$DEST/start-es-v2-diag.sh"
echo "$VERSION" > "$DEST/VERSION"
log "Skripte kopiert nach $DEST"

if [ -d "$SRC/theme/dii-ess-aye-rgds-plus" ]; then
    mkdir -p "$THEMEDIR"
    rm -rf "$THEMEDIR/dii-ess-aye-rgds-plus.new"
    cp -r "$SRC/theme/dii-ess-aye-rgds-plus" "$THEMEDIR/dii-ess-aye-rgds-plus.new" || fail "Could not copy the theme."
    rm -rf "$THEMEDIR/dii-ess-aye-rgds-plus"
    mv "$THEMEDIR/dii-ess-aye-rgds-plus.new" "$THEMEDIR/dii-ess-aye-rgds-plus"
    log "Theme kopiert: $THEMEDIR/dii-ess-aye-rgds-plus"
fi

for f in "$SRC"/ports/*.sh; do
    cp "$f" "$PORTS/" && chmod +x "$PORTS/$(basename "$f")" 2>/dev/null
    log "Ports-Eintrag: $(basename "$f")"
done

# --- 3. Installer entfernen und auf Dual umschalten ---
rm -f "$PORTS/Install ROCKNIX DualStation.sh"
rm -rf "$SRC"
log "Installer-Dateien entfernt"

log "Umschalten auf Dual"
/bin/bash "$DEST/es-switch-helper.sh" dual
log "=== Installation fertig ==="
exit 0
