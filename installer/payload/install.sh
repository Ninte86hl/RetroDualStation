#!/bin/bash
# RDS – Installation
# Aufruf: systemd-run --no-block /bin/bash <ports>/.dualstation/install.sh <ports>
#
# 1. Pruefen: RG DS Plus oder RG DS (DSI-1 + DSI-2 gleich gross), ES-Binary laeuft auf
#    dieser ROCKNIX-Version (keine fehlenden Bibliotheken)
# 2. Dateien nach /storage/rds-install, Theme, Ports-Eintraege kopieren
# 3. Installer-Dateien entfernen und auf Dual umschalten

PORTS="${1:-/storage/roms/ports}"
SRC="$PORTS/.dualstation"
DEST=/storage/rds-install
OLDDEST=/storage/rgds-test        # Name bis v15.1 – wird beim Update umbenannt
THEMEDIR=/storage/.config/emulationstation/themes
ESCFG=/storage/.config/emulationstation/es_settings.cfg
LOG=/storage/dualstation-install.log
export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock

VERSION="$(cat "$SRC/VERSION" 2>/dev/null)"
BIN=emulationstation-rgds
# Neuinstallation oder Update? (VERSION schreibt nur eine abgeschlossene Installation)
OLDVER="$(cat "$DEST/VERSION" 2>/dev/null || cat "$OLDDEST/VERSION" 2>/dev/null)"
if [ -n "$OLDVER" ]; then MODE=update; else MODE=install; fi

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

# Meldung in ES anzeigen (ES-HTTP-Schnittstelle, Port 1234)
notify()  { curl -s -m 3 -X POST -H 'Content-Type: text/plain' --data "$1" http://127.0.0.1:1234/notify >/dev/null 2>&1; }
msgbox()  { curl -s -m 3 -X POST -H 'Content-Type: text/plain' --data "$1" http://127.0.0.1:1234/messagebox >/dev/null 2>&1; }

fail() {
    log "ABBRUCH: $1"
    msgbox "RDS: $1 Nothing was changed. Log: $LOG"
    exit 1
}

if [ "$MODE" = update ]; then
    log "=== Update RDS $OLDVER -> $VERSION ==="
else
    log "=== Neuinstallation RDS $VERSION ==="
fi
log "Quelle: $SRC"
grep -E '^(NAME|VERSION|VERSION_ID|BUILD_ID)=' /etc/os-release 2>/dev/null | while read -r l; do log "os-release: $l"; done

# --- 1. Pruefungen (ES laeuft noch, Meldungen sind sichtbar) ---
[ -n "$BIN" ] && [ -f "$SRC/$BIN" ] || fail "Installer files are incomplete (.dualstation folder missing?)."

OUTPUTS="$(swaymsg -t get_outputs -r 2>/dev/null)"
MODEL="$(tr -d '\0' < /proc/device-tree/model 2>/dev/null)"
log "Modell: $MODEL"
case "$(tr '\0' ' ' < /proc/device-tree/compatible 2>/dev/null)" in
    *anbernic,rg-ds-plus*) DEVICE="RG DS Plus" ;;
    *anbernic,rg-ds*)      DEVICE="RG DS" ;;
    *)                     DEVICE="" ;;
esac
# Bildschirm-Bereiche aus Sway: DSI-2 = oben, DSI-1 = unten, gleich groß (relativ zum ES-Fenster)
SCREENDATA="$(printf '%s' "$OUTPUTS" | python3 -c '
import json, sys
o = {x["name"]: x["rect"] for x in json.load(sys.stdin) if x.get("active")}
t, b = o.get("DSI-2"), o.get("DSI-1")
if not (t and b) or (t["width"], t["height"]) != (b["width"], b["height"]):
    sys.exit(1)
x0, y0 = min(t["x"], b["x"]), min(t["y"], b["y"])
print("top=%d,%d,%d,%d" % (t["x"] - x0, t["y"] - y0, t["width"], t["height"]))
print("bottom=%d,%d,%d,%d" % (b["x"] - x0, b["y"] - y0, b["width"], b["height"]))' 2>>"$LOG")"
if [ -z "$DEVICE" ] || [ -z "$SCREENDATA" ]; then
    log "Ausgaenge: $(printf '%s' "$OUTPUTS" | tr -d '\n' | head -c 600)"
    fail "This version supports the Anbernic RG DS Plus and RG DS (two screens of equal size)."
fi
log "Geraet: $DEVICE erkannt ($(echo $SCREENDATA))"

# Bildschirm-Bereiche fuer ES (Patch 004/005); eigene Anpassungen bleiben erhalten,
# solange sie zur aktuellen Bildschirmgroesse passen
SCREENS=/storage/.config/retrodualstation/screens.cfg
if [ -f "$SCREENS" ] && ! grep -q "$(printf '%s' "$SCREENDATA" | head -1 | cut -d, -f3-)" "$SCREENS"; then
    mv -f "$SCREENS" "$SCREENS.alt"
    log "screens.cfg passte nicht zum Geraet -> screens.cfg.alt"
fi
if [ ! -f "$SCREENS" ]; then
    mkdir -p /storage/.config/retrodualstation
    { echo "# RetroDualStation: Bildschirm-Bereiche im ES-Fenster (x,y,Breite,Hoehe)"
      echo "# $DEVICE (vom Installer aus Sway ermittelt)"
      printf '%s\n' "$SCREENDATA"
      echo "menu=top"; } > "$SCREENS"
    log "screens.cfg angelegt ($DEVICE)"
fi

chmod +x "$SRC/$BIN" 2>/dev/null
cp "$SRC/$BIN" /tmp/dualstation-bincheck && chmod +x /tmp/dualstation-bincheck
MISSING="$(ldd /tmp/dualstation-bincheck 2>&1 | grep 'not found')"
rm -f /tmp/dualstation-bincheck
if [ -n "$MISSING" ]; then
    log "Fehlende Bibliotheken: $MISSING"
    fail "The included EmulationStation does not match this ROCKNIX version."
fi
log "ES-Binary: $BIN, Bibliotheken ok"

if [ "$MODE" = update ]; then
    notify "Updating RDS $OLDVER → $VERSION – EmulationStation will restart in a moment..."
else
    notify "Installing RDS – EmulationStation will restart in a moment..."
fi
sleep 2

# --- 2. Dateien kopieren ---
# Update von v15.1 oder älter: Programmordner umbenennen (gemerkte Themes, Sicherungen und Log ziehen mit).
# Übergangsweise zeigt der alte Name dorthin, bis der Helfer am Ende ES vom neuen Ort startet.
if [ -d "$OLDDEST" ] && [ ! -L "$OLDDEST" ] && [ ! -e "$DEST" ]; then
    mv "$OLDDEST" "$DEST" || fail "Could not rename $OLDDEST."
    ln -s "$DEST" "$OLDDEST"
    log "Programmordner umbenannt: $OLDDEST -> $DEST"
fi
mkdir -p "$DEST" || fail "Could not create $DEST."

if [ -f "$ESCFG" ] && [ ! -f "$DEST/es_settings.before-install.cfg" ]; then
    cp "$ESCFG" "$DEST/es_settings.before-install.cfg"
    log "Sicherung: $DEST/es_settings.before-install.cfg"
fi

# Binary ueber Zwischennamen, damit ein laufendes ES nicht stoert
cp "$SRC/$BIN" "$DEST/.$BIN.new" && chmod +x "$DEST/.$BIN.new" && mv -f "$DEST/.$BIN.new" "$DEST/$BIN" \
    || fail "Could not copy $BIN."
# Dateien aelterer Versionen (mit Versionsnummer im Namen) entfernen
for old in "$DEST"/emulationstation-rgds-* "$DEST"/start-es-v2-diag.sh; do
    [ -f "$old" ] && rm -f "$old" && log "entfernt: $old"
done

for f in start-es-dualstation.sh rgds-sway-fix.sh es-switch-helper.sh rgds-diag.sh uninstall.sh rds-settings.py rds-migrate-savestates.py; do
    cp "$SRC/rds-install/$f" "$DEST/$f" || fail "Could not copy $f."
    chmod +x "$DEST/$f"
done
echo "$VERSION" > "$DEST/VERSION"
log "Skripte kopiert nach $DEST"

# --- Originalwerte sichern, bevor RDS etwas ändert (uninstall.sh setzt sie zurück) ---
# Je Einstellung nur beim ersten Mal gemerkt; Sicherungen älterer RDS-Versionen (*.vor-rds-kuerzel, *.before-rds)
# liefern dabei die Werte von vor RDS. Werte aus system.cfg (set_setting) merken die Blöcke weiter unten selbst.
BK="$DEST/settings-before-rds.json"
rs() { python3 "$DEST/rds-settings.py" "$@" >>"$LOG" 2>&1 || log "WARNUNG: Sicherung fehlgeschlagen: $*"; }
RACFG=/storage/.config/retroarch/retroarch.cfg
DCFG=/storage/.config/drastic/config/drastic.cfg
DSPINI=/storage/.config/dsperate/dsperate.ini
ESINPUT=/storage/.emulationstation/es_input.cfg
rs save "$BK" "$RACFG" kv confirm_reset confirm_close notification_show_save_state video_font_enable \
    menu_enable_widgets network_cmd_enable quit_press_twice input_enable_hotkey_btn input_toggle_fast_forward_btn \
    input_save_state_btn input_load_state_btn input_rewind_btn input_menu_toggle_btn input_fps_toggle_btn \
    input_exit_emulator_btn input_state_slot_decrease_btn input_state_slot_increase_btn --legacy "$RACFG.vor-rds-kuerzel"
rs save "$BK" "$DSPINI" kv modifier quit pause fast_forward fast_forward_toggle save_state load_state slot_next \
    slot_prev layout_next layout_prev screen_swap fps stylus_axis toasts --legacy "$DSPINI.vor-rds-kuerzel"
rs save "$BK" "$DCFG" kv "controls_a[CONTROL_INDEX_MENU]" "controls_b[CONTROL_INDEX_MENU]" \
    "controls_a[CONTROL_INDEX_FAST_FORWARD]" "controls_b[CONTROL_INDEX_FAST_FORWARD]" compress_savestates \
    "controls_a[CONTROL_INDEX_SAVE_STATE]" "controls_b[CONTROL_INDEX_SAVE_STATE]" \
    "controls_a[CONTROL_INDEX_LOAD_STATE]" "controls_b[CONTROL_INDEX_LOAD_STATE]" \
    --legacy "$DCFG.vor-rds-kuerzel"
rs save "$BK" "$ESCFG" esxml GameTransitionStyle --legacy "$DEST/es_settings.before-install.cfg"
[ "$DEVICE" = "RG DS Plus" ] && rs save-esinput "$BK" "$ESINPUT" --legacy "$ESINPUT.before-rds"
# Notfall-Sicherung der ganzen Dateien (nur beim ersten Mal; nach erfolgreicher Deinstallation entfernt).
# Format wie ROCKNIX' backuptool: umbenannt in ROCKNIX_BACKUP.zip stellt „backuptool restore“ sie zurück.
# Zwei Kopien: intern (immer sofort da – roms hängt ROCKNIX beim Start erst nach unseren Diensten ein) für die
# automatische Wiederherstellung, und in roms/backup sichtbar für den Nutzer.
RDSZIP=/storage/roms/backup/RDS_ORIGINAL_BACKUP.zip
RDSZIPI=/storage/.config/rds-backup/RDS_ORIGINAL_BACKUP.zip
if [ ! -f "$RDSZIPI" ] && [ -f "$RDSZIP" ]; then
    mkdir -p "${RDSZIPI%/*}" && cp "$RDSZIP" "$RDSZIPI" && log "Notfall-Sicherung intern abgelegt: $RDSZIPI"
fi
if [ ! -f "$RDSZIPI" ]; then
    [ "$MODE" = update ] && log "Hinweis: Notfall-Sicherung wird beim Update angelegt – Stand von vor RDS nur, soweit aeltere Sicherungen ihn enthalten"
    rs snapshot "$RDSZIPI" "$RACFG=$RACFG.vor-rds-kuerzel" "$DCFG=$DCFG.vor-rds-kuerzel" "$DSPINI=$DSPINI.vor-rds-kuerzel" \
        "$ESCFG=$DEST/es_settings.before-install.cfg" "$ESINPUT=$ESINPUT.before-rds" \
        /storage/.config/system/configs/system.cfg /storage/.config/sway/config /storage/.config/mako/config
fi
if [ -f "$RDSZIPI" ] && [ ! -f "$RDSZIP" ]; then
    mkdir -p "${RDSZIP%/*}" && cp "$RDSZIPI" "$RDSZIP"
fi
if [ -f "$RDSZIP" ] && [ ! -f "${RDSZIP%.zip}.txt" ]; then
    cat > "${RDSZIP%.zip}.txt" <<'TXT'
RetroDualStation (RDS) – Sicherung der Einstellungen von vor der ersten Installation
=====================================================================================
RDS_ORIGINAL_BACKUP.zip enthält RetroArch, DraStic, DSperate, EmulationStation (Einstellungen und Tastenbelegung),
system.cfg, Sway und mako im Zustand vor RDS. Die Deinstallation setzt diese Werte normalerweise selbst zurück –
diese Datei ist nur für den Notfall gedacht.

Wiederherstellen (überschreibt diese Dateien komplett, spätere eigene Änderungen daran gehen verloren):
  1. Eine vorhandene ROCKNIX_BACKUP.zip in diesem Ordner umbenennen (sonst geht sie verloren).
  2. RDS_ORIGINAL_BACKUP.zip kopieren und die Kopie in ROCKNIX_BACKUP.zip umbenennen.
  3. Die Wiederherstellung von ROCKNIX ausführen (per SSH: backuptool restore), danach neu starten.

Restore (overwrites these files completely): rename an existing ROCKNIX_BACKUP.zip first, copy
RDS_ORIGINAL_BACKUP.zip to ROCKNIX_BACKUP.zip, then run the ROCKNIX restore (via SSH: backuptool restore), reboot.
TXT
fi

if [ -d "$SRC/theme/dii-ess-aye-rds" ]; then
    mkdir -p "$THEMEDIR"
    rm -rf "$THEMEDIR/dii-ess-aye-rds.new"
    cp -r "$SRC/theme/dii-ess-aye-rds" "$THEMEDIR/dii-ess-aye-rds.new" || fail "Could not copy the theme."
    rm -rf "$THEMEDIR/dii-ess-aye-rds"
    mv "$THEMEDIR/dii-ess-aye-rds.new" "$THEMEDIR/dii-ess-aye-rds"
    log "Theme kopiert: $THEMEDIR/dii-ess-aye-rds"
fi

# Themes hießen bis v13.1 "...-rgds-plus" – auf die geräteneutralen Namen umziehen (Auswahl und Ansichten bleiben)
ESTH=/storage/.config/emulationstation
for pair in "dii-ess-aye-rgds-plus:dii-ess-aye-rds" "canvas-ds-rgds-plus:canvas-rds"; do
    o="${pair%%:*}"; n="${pair#*:}"
    # nur entfernen, wenn der neue Name wirklich da ist (Paket oder schon installiert) – sonst bliebe kein Theme
    if [ -d "$THEMEDIR/$o" ] && { [ -d "$SRC/theme/$n" ] || [ -d "$THEMEDIR/$n" ]; }; then
        rm -rf "$THEMEDIR/$o" && log "altes Theme entfernt: $o"
    fi
    [ -f "$ESTH/themesettings/$o.cfg" ] && [ ! -f "$ESTH/themesettings/$n.cfg" ] && mv "$ESTH/themesettings/$o.cfg" "$ESTH/themesettings/$n.cfg"
    for tf in "$DEST/theme.dual" "$DEST/theme.single"; do
        [ -f "$tf" ] && grep -qx "$o" "$tf" && echo "$n" > "$tf" && log "Theme-Auswahl: $o -> $n"
    done
done

for f in "$SRC"/ports/*.sh; do
    cp "$f" "$PORTS/" && chmod +x "$PORTS/$(basename "$f")" 2>/dev/null
    log "Ports-Eintrag: $(basename "$f")"
done

# canvas-ds (Standard-Theme im Dual-Modus, falls im Paket)
if [ -d "$SRC/theme/canvas-rds" ]; then
    rm -rf "$THEMEDIR/canvas-rds.new"
    mv "$SRC/theme/canvas-rds" "$THEMEDIR/canvas-rds.new" || fail "Could not copy canvas-ds (not enough space?)."
    rm -rf "$THEMEDIR/canvas-rds"
    mv "$THEMEDIR/canvas-rds.new" "$THEMEDIR/canvas-rds"
    [ -f "$DEST/theme.dual" ] || echo canvas-rds > "$DEST/theme.dual"
    log "Theme kopiert: canvas-rds (Standard im Dual-Modus: $(cat "$DEST/theme.dual"))"
fi

# Ports-Einträge vor v14 hießen anders (ROCKNIX DualStation / RGDS) – alte Dateien entfernen
for old in "RGDS Dual-Screen ES.sh" "RGDS Single-Screen ES.sh" "Uninstall ROCKNIX DualStation.sh" \
           "RDS Dual-Screen ES.sh" "RDS Single-Screen ES.sh"; do
    [ -f "$PORTS/$old" ] && rm -f "$PORTS/$old" && log "alter Ports-Eintrag entfernt: $old"
done

# Ports-Liste: Name, Beschreibung, Version, Datum, Entwickler und Icon (gamelist.xml; andere Einträge bleiben)
RDSDATE="$(cat "$SRC/DATE" 2>/dev/null | tr -d '\n')"
if [ -d "$SRC/images" ]; then
    mkdir -p "$PORTS/images"
    cp "$SRC"/images/rds-*.png "$PORTS/images/"
    RDSLANG="$( . /etc/profile >/dev/null 2>&1; get_setting system.language )"
    # „Install RDS.sh“ heißt nach der Installation „Update RDS“: ein später kopiertes neues Paket erscheint so als
    # Update. Die Deinstallation entfernt den Eintrag wieder – auf einem frischen Gerät steht dann „Install RDS“.
    python3 - "$PORTS/gamelist.xml" "$VERSION" "${RDSDATE:-$(date +%Y%m%d)}" "$RDSLANG" <<'PY' 2>>"$LOG"
import os, sys, xml.etree.ElementTree as ET
f, version, date = sys.argv[1], sys.argv[2], sys.argv[3]
de = (sys.argv[4] if len(sys.argv) > 4 else "").startswith("de")   # Sprache von ES bei der Installation
root = ET.parse(f).getroot() if os.path.exists(f) and os.path.getsize(f) else ET.Element("gameList")
old = {"./RGDS Dual-Screen ES.sh", "./RGDS Single-Screen ES.sh", "./RDS Dual-Screen ES.sh", "./RDS Single-Screen ES.sh", "./Uninstall ROCKNIX DualStation.sh",
       "./Install ROCKNIX DualStation.sh"}
for g in [g for g in root.findall("game") if g.findtext("path") in old]:
    root.remove(g)
v = "RDS %s" % version
entries = {
    "RDS Dual-Screen.sh": ("RDS Dual-Screen", "rds-dual.png",
        "Startet EmulationStation über beide Bildschirme (RetroDualStation). / Runs EmulationStation across both screens."),
    "RDS Single-Screen.sh": ("RDS Single-Screen", "rds-single.png",
        "Zurück zum Original-ES von ROCKNIX auf einem Bildschirm, z. B. zum Scrapen. / Back to stock ROCKNIX ES on one screen, e.g. for scraping."),
    "Artwork Manager.sh": ("Artwork Manager", "rds-artwork.png",
        "Boxart, Icon und Hero-Bild für deine Spiele direkt am Gerät suchen und anpassen. / Find and fit boxart, icons and hero images on the device."),
    "Uninstall RDS.sh": ("Uninstall RDS", "rds-uninstall.png",
        "Entfernt RDS und stellt das Original-ES samt Theme wieder her. Spiele und Spielstände bleiben. / Removes RDS and restores stock ES; games and saves stay."),
    "Install RDS.sh": ("Update RDS", "rds-install.png",
        "Aktualisiert RDS auf die neue Version – Einstellungen, Spielstände und Sicherungen bleiben. / Updates RDS to the new version – settings, saves and backups stay."),
}
for script, (name, img, desc) in entries.items():
    path = "./" + script
    g = next((g for g in root.findall("game") if g.findtext("path") == path), None)
    if g is None:
        g = ET.SubElement(root, "game")
        ET.SubElement(g, "path").text = path
    for tag, val in (("name", name), ("desc", "%s\n\n%s" % (v, desc.split(" / ")[0 if de else 1])), ("image", "./images/" + img),
                     ("thumbnail", "./images/" + img), ("releasedate", date + "T000000"),
                     ("developer", "Ninte86hl"), ("publisher", "RetroDualStation"), ("genre", "Tool")):
        e = g.find(tag)
        if e is None:
            e = ET.SubElement(g, tag)
        e.text = val
ET.indent(root)
ET.ElementTree(root).write(f, encoding="utf-8", xml_declaration=True)
PY
    log "Ports-Liste: Namen, Beschreibung, Version und Icons gesetzt"
fi

# --- 2b. Kontrollcenter ---
CCDIR=/storage/.config/retrodualstation/controlcenter
SYSD=/storage/.config/system.d
if [ -f "$SRC/controlcenter/rds_cc.py" ]; then
    mkdir -p "$CCDIR" "$SYSD/essway.service.wants" /storage/.config/logind.conf.d
    cp "$SRC/controlcenter/rds_cc.py" "$CCDIR/rds_cc.py" || fail "Could not copy the control center."
    if [ -d "$SRC/controlcenter/tour" ]; then   # Bilder der Tour (läuft einmal nach der Installation)
        mkdir -p "$CCDIR/tour" && cp "$SRC"/controlcenter/tour/*.png "$CCDIR/tour/"
        rm -f /storage/.config/retrodualstation/tour.done
    fi
    rm -rf "$CCDIR/__pycache__" /storage/.config/rds-controlcenter   # alter Testordner
    cp "$SRC/controlcenter/rds-controlcenter.service" "$SYSD/"
    cp "$SRC/controlcenter/rds-resume.service" "$SYSD/"
    ln -sf "$SYSD/rds-controlcenter.service" "$SYSD/essway.service.wants/rds-controlcenter.service"
    for t in suspend hibernate hybrid-sleep; do
        mkdir -p "$SYSD/$t.target.wants"
        ln -sf "$SYSD/rds-resume.service" "$SYSD/$t.target.wants/rds-resume.service"
    done
    cp "$SRC/controlcenter/rds-logind-powerkey.conf" /storage/.config/logind.conf.d/
    # Absicherung der Deinstallation: bricht sie ab, bevor die Einstellungen zurückgesetzt sind, stellt dieser
    # Dienst beim nächsten Start die Notfall-Sicherung wieder her (nur mit Merker, sonst tut er nichts)
    cat > "$SYSD/rds-uninstall-guard.service" <<'UNIT'
# RetroDualStation: unterbrochene Deinstallation – Einstellungen von vor RDS wiederherstellen
[Unit]
Description=RetroDualStation – Einstellungen nach unterbrochener Deinstallation wiederherstellen
ConditionPathExists=/storage/.config/rds-uninstall.running
Before=essway.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'Z=/storage/.config/rds-backup/RDS_ORIGINAL_BACKUP.zip; [ -f "$$Z" ] || Z=/storage/roms/backup/RDS_ORIGINAL_BACKUP.zip; L=/storage/dualstation-uninstall.log; if [ -f "$$Z" ] && unzip -o "$$Z" -d / >>"$$L" 2>&1; then rm -f /storage/.config/rds-uninstall.running; echo "$$(date) Start: Notfall-Sicherung wiederhergestellt" >>"$$L"; else echo "$$(date) Start: Wiederherstellung fehlgeschlagen" >>"$$L"; fi'

[Install]
WantedBy=multi-user.target
UNIT
    mkdir -p "$SYSD/multi-user.target.wants"
    ln -sf "$SYSD/rds-uninstall-guard.service" "$SYSD/multi-user.target.wants/rds-uninstall-guard.service"
    systemctl daemon-reload
    systemctl kill -s HUP systemd-logind 2>/dev/null   # Power-Taste übernimmt das CC
    log "Kontrollcenter installiert: $CCDIR"

    # Geräteeinstellungen (Rückgängig in uninstall.sh)
    # /etc/profile nur in einer Subshell laden (setzt sonst eigene Variablen / beendet das Skript)
    if [ ! -f "$DEST/bottomscreen.before" ]; then
        ( . /etc/profile >/dev/null 2>&1; get_setting rocknix.bottomscreen.type ) > "$DEST/bottomscreen.before" 2>/dev/null
    fi
    ( . /etc/profile >/dev/null 2>&1; set_setting rocknix.bottomscreen.type none ) >/dev/null 2>&1   # lowerdeck aus
    log "lowerdeck aus (vorher: $(cat "$DEST/bottomscreen.before" 2>/dev/null))"

    SWAYCFG=/storage/.config/sway/config
    if [ -f "$SWAYCFG" ] && ! grep -q 'Fake_Keyboard' "$SWAYCFG"; then
        printf '\n# RetroDualStation: gptokeyb-Tastatur an den oberen Screen (Ports steuerbar)\nseat seat0 attach "4660:22136:Fake_Keyboard"\n' >> "$SWAYCFG"
        log "Sway: Fake_Keyboard an seat0"
    fi
    swaymsg seat seat0 attach "4660:22136:Fake_Keyboard" >/dev/null 2>&1   # sofort wirksam
    if [ -f "$SWAYCFG" ] && ! grep -q 'RDS_Keys' "$SWAYCFG"; then
        printf '\n# RetroDualStation: virtuelle Tasten des Kontrollcenters an die Spiele\nseat seat0 attach "21060:21297:RDS_Keys"\n' >> "$SWAYCFG"
    fi

    # RetroArch: keine Rückfragen bei Neustart/Beenden, keine Speicherstand-Einblendung (Gameswitcher)
    RACFG=/storage/.config/retroarch/retroarch.cfg
    if [ -f "$RACFG" ] && ! pidof retroarch >/dev/null; then
        # Ersetzen oder hinzufügen: fehlt eine Zeile (frisches ROCKNIX oder nach einer Deinstallation, die sie wieder
        # entfernt hat), gilt sonst der RetroArch-Standard. (RetroArch 1.22 kennt confirm_reset nicht mehr und fragt
        # beim Neustart trotzdem nach – das CC sendet RESET deshalb zweimal, siehe ra_reset.)
        # Netzbefehle (Port 55355, nur lokal genutzt): Kontrollcenter/Gameswitcher speichern, laden, neu starten
        # und beenden darüber – bei frischem ROCKNIX sind sie aus
        for kv in 'confirm_reset=false' 'confirm_close=false' 'notification_show_save_state=false' \
                  'video_font_enable=false' 'menu_enable_widgets=false' 'network_cmd_enable=true' 'quit_press_twice=false'; do
            k="${kv%%=*}"; v="${kv#*=}"
            if grep -q "^$k = " "$RACFG"; then sed -i "s/^$k = .*/$k = \"$v\"/" "$RACFG"; else echo "$k = \"$v\"" >> "$RACFG"; fi
        done
        log "RetroArch: Rueckfragen und Einblendungen aus (Erfolgsmeldung zeigt das Kontrollcenter)"
    fi
    # Einheitliche Kürzel (Anbernic + R1 Vorspulen, R2 Speichern, L2 Laden, X Menü, Y FPS, Start Beenden).
    # Nur einmal pro Gerät (Merker), vorher Sicherung; eigene spätere Änderungen bleiben unangetastet.
    KMARK=/storage/.config/retrodualstation/kuerzel.done
    if [ ! -f "$KMARK" ] && [ -f "$RACFG" ] && ! pidof retroarch >/dev/null; then
        cp "$RACFG" "$RACFG.vor-rds-kuerzel"
        set_ra(){ if grep -q "^$1 = " "$RACFG"; then sed -i "s/^$1 = .*/$1 = \"$2\"/" "$RACFG"; else echo "$1 = \"$2\"" >> "$RACFG"; fi; }
        set_ra input_enable_hotkey_btn 10; set_ra input_toggle_fast_forward_btn 5; set_ra input_save_state_btn 7
        set_ra input_load_state_btn 6; set_ra input_rewind_btn 4; set_ra input_menu_toggle_btn 2
        set_ra input_fps_toggle_btn 3; set_ra input_exit_emulator_btn 9
        set_ra input_state_slot_decrease_btn 15; set_ra input_state_slot_increase_btn 16
        DSPINI=/storage/.config/dsperate/dsperate.ini
        if [ -f "$DSPINI" ] && ! pidof dsperate >/dev/null; then
            cp "$DSPINI" "$DSPINI.vor-rds-kuerzel"
            sed -i -e 's/^modifier = .*/modifier = guide/' -e 's/^quit = .*/quit = mod+start/' \
                   -e 's/^pause = .*/pause = mod+x/' -e 's/^fast_forward = .*/fast_forward = none/' \
                   -e 's/^fast_forward_toggle = .*/fast_forward_toggle = mod+rightshoulder/' \
                   -e 's/^save_state = .*/save_state = mod++righttrigger/' -e 's/^load_state = .*/load_state = mod++lefttrigger/' \
                   -e 's/^slot_next = .*/slot_next = mod+dpright/' -e 's/^slot_prev = .*/slot_prev = mod+dpleft/' \
                   -e 's/^layout_next = .*/layout_next = mod+back/' -e 's/^layout_prev = .*/layout_prev = mod+dpdown/' \
                   -e 's/^screen_swap = .*/screen_swap = mod+dpup/' -e 's/^fps = .*/fps = mod+y/' "$DSPINI"
        fi
        mkdir -p /storage/.config/retrodualstation && date > "$KMARK"
        log "Kuerzel: einheitliches Schema gesetzt (Sicherungen *.vor-rds-kuerzel)"
    fi
    # DraStic: Menü und Vorspulen auf Tasten, die es am Gerät nicht gibt – F11 (324) und F12 (325)
    # der virtuellen Tastatur des Kontrollcenters. Stick, L3 und R3 bleiben frei; die Anbernic-Taste
    # gehört dem CC. (Bis v14: R3 und Phantom-Achse – auf dem RG DS Plus sprang Vorspulen beim
    # Linksdrücken an.) Einmal je Gerät (Merker v2), Sicherung nur bei der ersten Umstellung.
    DMARK=/storage/.config/retrodualstation/drastic-kuerzel.done
    DMARK2=/storage/.config/retrodualstation/drastic-kuerzel-v2.done
    DCFG=/storage/.config/drastic/config/drastic.cfg
    if [ ! -f "$DMARK2" ] && [ -f "$DCFG" ] && ! pidof drastic >/dev/null; then
        [ -f "$DMARK" ] || cp "$DCFG" "$DCFG.vor-rds-kuerzel"
        sed -i -E -e 's/^(controls_[ab]\[CONTROL_INDEX_MENU\]) = .*/\1 = 324/' \
                  -e 's/^(controls_[ab]\[CONTROL_INDEX_FAST_FORWARD\]) = .*/\1 = 325/' "$DCFG"
        mkdir -p /storage/.config/retrodualstation && date > "$DMARK2" && date > "$DMARK"
        log "DraStic: Menue auf F11, Vorspulen auf F12 (virtuelle Tasten, nur ueber das CC)"
    fi
    # DraStic: Speichern/Laden auf F9 (322) / F10 (323) der virtuellen Tastatur – ROCKNIX legt sie auf R2/L2 allein,
    # DraStic kennt keine Kombinationen. Anbernic + R2/L2 übersetzt das CC; R2/L2 allein tun nichts mehr. Einmal je Gerät.
    DMARK3=/storage/.config/retrodualstation/drastic-kuerzel-v3.done
    if [ ! -f "$DMARK3" ] && [ -f "$DCFG" ] && ! pidof drastic >/dev/null; then
        sed -i -E -e 's/^(controls_[ab]\[CONTROL_INDEX_SAVE_STATE\]) = .*/\1 = 322/' \
                  -e 's/^(controls_[ab]\[CONTROL_INDEX_LOAD_STATE\]) = .*/\1 = 323/' "$DCFG"
        mkdir -p /storage/.config/retrodualstation && date > "$DMARK3"
        log "DraStic: Speichern auf F9, Laden auf F10 (Anbernic + R2/L2 ueber das CC)"
    fi
    # DraStic: Savestates unkomprimiert – Speichern ≈0,3 s statt 1,8 s (Gameswitcher, Home kurz).
    # Nur wenn DraStic nicht läuft (es schreibt die Datei beim Beenden zurück).
    # TODO: prüfen, ob alte komprimierte Stände danach noch laden (Test 25.10. lief mit gelöschten Ständen).
    if [ -f "$DCFG" ] && ! pidof drastic >/dev/null && ! grep -q '^compress_savestates *= *0' "$DCFG"; then
        if grep -q '^compress_savestates' "$DCFG"; then
            sed -i -E 's/^compress_savestates *= *.*/compress_savestates = 0/' "$DCFG"
        else
            echo "compress_savestates = 0" >> "$DCFG"
        fi
        log "DraStic: Savestates unkomprimiert (schnelleres Speichern)"
    fi
    # Savestates einmalig auf das Schema ab v15.2 umziehen (Platz 0 = automatisch, Slots 1–9 = Emulator-Plätze).
    # Update von v15.1 oder älter: Gameswitcher-Stand und Nutzer-Platz 0 tauschen; Neuinstallation: eigene Stände
    # von Platz 0 in freie Slots. Wer schon mit v15.2 gespielt hat, hat das neue Schema – dort nichts tun.
    SMMARK=/storage/.config/retrodualstation/savestates-v15.2.done
    if [ ! -f "$SMMARK" ] && ! pidof retroarch drastic dsperate >/dev/null; then
        case "$OLDVER" in
            v15.2*|v15.[3-9]*|v1[6-9]*|v[2-9][0-9]*) SMARG=skip ;;
            "") SMARG=--fresh ;;
            *)  SMARG= ;;
        esac
        if [ "$SMARG" != skip ]; then
            python3 "$DEST/rds-migrate-savestates.py" $SMARG >>"$LOG" 2>&1 \
                && log "Savestates auf Slots 1-9 umgezogen (${SMARG:-Update von $OLDVER})" \
                || log "WARNUNG: Umzug der Savestates fehlgeschlagen"
        fi
        mkdir -p /storage/.config/retrodualstation && date > "$SMMARK"
    fi
    # Schnellwechsel standardmäßig an (ab v15.2) – einmal je Gerät; danach entscheidet der Schalter im CC
    FSMARK=/storage/.config/retrodualstation/fastswitch-default.done
    if [ ! -f "$FSMARK" ]; then
        mkdir -p /storage/.config/retrodualstation
        touch /storage/.config/retrodualstation/fastswitch && date > "$FSMARK"
        log "Schnellwechsel: an (im Kontrollcenter oben abschaltbar)"
    fi
    # ES-Savestate-Manager aus: Speicherplätze verwaltet das Kontrollcenter (einmalig, alter Wert gemerkt)
    SSMARK=/storage/.config/retrodualstation/savestates.done
    if [ ! -f "$SSMARK" ]; then
        SSOLD="$( . /etc/profile >/dev/null 2>&1; get_setting global.savestates )"
        ( . /etc/profile >/dev/null 2>&1; set_setting global.savestates auto ) >/dev/null 2>&1
        echo "$SSOLD" > "$SSMARK"
        log "ES: Savestate-Manager aus (vorher: ${SSOLD:-Standard})"
    fi
    # ROCKNIX-Hotkeys aus der Controller-Datei überdecken sonst unser Kürzel-Schema (RG DS: L1/R1/R2)
    AHMARK=/storage/.config/retrodualstation/autohotkeys.done
    if [ ! -f "$AHMARK" ]; then
        AHOLD="$( . /etc/profile >/dev/null 2>&1; get_setting system.autohotkeys )"
        ( . /etc/profile >/dev/null 2>&1; set_setting system.autohotkeys 0 ) >/dev/null 2>&1
        echo "$AHOLD" > "$AHMARK"
        log "RetroArch: automatische Hotkeys von ROCKNIX aus (vorher: ${AHOLD:-Standard})"
    fi
    # DSperate auf dem RG DS Plus: Der Treiber spiegelt links/rechts des Sticks auf die Achsen des
    # fehlenden rechten Sticks – der Touch-Cursor (stylus_axis = right) wanderte beim Steuern mit.
    if [ "$DEVICE" = "RG DS Plus" ] && [ -f /storage/.config/dsperate/dsperate.ini ] && ! pidof dsperate >/dev/null \
       && grep -q '^stylus_axis = right' /storage/.config/dsperate/dsperate.ini; then
        sed -i 's/^stylus_axis = right/stylus_axis = none/' /storage/.config/dsperate/dsperate.ini
        log "DSperate (RG DS Plus): Touch-Cursor auf dem Phantom-Stick aus"
    fi
    # ES auf dem RG DS Plus: dieselben Phantom-Achsen kamen in ES als zweiter Stick an – zwei Bewegungen
    # und zwei Loslass-Signale je Stickdruck, das Karussell der Systemliste blieb dabei stehen.
    # Nur den Phantom-Stick des eingebauten Joypads austragen (vorher einmal sichern).
    ESINPUT=/storage/.emulationstation/es_input.cfg
    if [ "$DEVICE" = "RG DS Plus" ] && [ -f "$ESINPUT" ] \
       && sed -n '/deviceName="retrogame_joypad"/,/<\/inputConfig>/p' "$ESINPUT" | grep -q rightanalog; then
        [ -f "$ESINPUT.before-rds" ] || cp "$ESINPUT" "$ESINPUT.before-rds"
        sed -i '/deviceName="retrogame_joypad"/,/<\/inputConfig>/{/rightanalog/d}' "$ESINPUT"
        log "ES (RG DS Plus): Phantom-Stick aus der Tastenbelegung entfernt"
    fi
    # DSperate: eigene Erfolgsmeldung aus – die Meldung oben kommt einheitlich vom Kontrollcenter
    DSPINI=/storage/.config/dsperate/dsperate.ini
    if [ -f "$DSPINI" ] && ! pidof dsperate >/dev/null && grep -q '^toasts = true' "$DSPINI"; then
        sed -i 's/^toasts = true/toasts = false/' "$DSPINI"
        log "DSperate: eigene Erfolgsmeldung aus (zeigt das Kontrollcenter)"
    fi
    # RetroAchievements: seit v13 über das Kontrollcenter unterstützt – nicht mehr abschalten.
    # Frühere Versionen hatten sie abgeschaltet: den damals gemerkten Wert einmalig zurückgeben.
    if [ -f "$DEST/retroachievements.before" ]; then
        RAOLD="$(cat "$DEST/retroachievements.before" 2>/dev/null)"
        RANOW="$( . /etc/profile >/dev/null 2>&1; get_setting global.retroachievements )"
        if [ "$RANOW" = "0" ] && [ -n "$RAOLD" ] && [ "$RAOLD" != "0" ]; then
            ( . /etc/profile >/dev/null 2>&1; set_setting global.retroachievements "$RAOLD" ) >/dev/null 2>&1
            log "ES: RetroAchievements wieder wie vor RetroDualStation ($RAOLD)"
        fi
        rm -f "$DEST/retroachievements.before"
    fi

    MAKOCFG=/storage/.config/mako/config
    if [ -f "$MAKOCFG" ] && ! grep -q 'RetroDualStation' "$MAKOCFG"; then
        printf '\n# RetroDualStation\n[summary~="^(Brightness|Volume):"]\ninvisible=1\n' >> "$MAKOCFG"
        log "mako: Helligkeit/Lautstaerke-Anzeige aus"
    fi
fi

# --- Artwork Manager (Ports) ---
# Programm nach ports/artworkmanager; settings.cfg, Sicherungen und Zwischenspeicher bleiben erhalten.
AMDIR="$PORTS/artworkmanager"
if [ -f "$SRC/artworkmanager/rds_artwork.py" ]; then
    mkdir -p "$AMDIR"
    cp "$SRC/artworkmanager/rds_artwork.py" "$SRC/artworkmanager/multidisc.py" "$AMDIR/"
    if [ -d "$SRC/artworkmanager/rocknixds_artwork_manager" ]; then
        rm -rf "$AMDIR/rocknixds_artwork_manager"
        cp -r "$SRC/artworkmanager/rocknixds_artwork_manager" "$AMDIR/"
    fi
    # iiSU-Rahmen mitliefern: das Gerät lädt so nie das große iiSU-Archiv (~100 MB im Speicher)
    if [ -f "$SRC/artworkmanager/borders/systems.txt" ]; then
        while read -r img dirs; do
            [ -f "$SRC/artworkmanager/borders/$img" ] || continue
            for sys in $dirs; do
                mkdir -p "$AMDIR/data/platform-borders/$sys"
                cp -n "$SRC/artworkmanager/borders/$img" "$AMDIR/data/platform-borders/$sys/"
                echo "iiSU borders shipped with RDS." > "$AMDIR/data/platform-borders/$sys/.iisu-archive-v1"
            done
        done < "$SRC/artworkmanager/borders/systems.txt"
        log "iiSU-Rahmen kopiert"
    fi
    rm -rf "$AMDIR/__pycache__"
    log "Artwork Manager kopiert: $AMDIR"
    # Pillow (Bildverarbeitung) für das Gerät
    LIBDIR=/storage/.config/retrodualstation/lib
    mkdir -p "$LIBDIR"
    if [ -f "$SRC/lib/pillow.whl" ]; then
        rm -rf "$LIBDIR/PIL" "$LIBDIR"/pillow*.dist-info "$LIBDIR/pillow.libs"
        ( cd "$LIBDIR" && python3 -m zipfile -e "$SRC/lib/pillow.whl" . ) && log "Pillow aus dem Paket installiert"
    elif ! PYTHONPATH="$LIBDIR" python3 -c "import PIL" 2>/dev/null; then
        ( cd "$LIBDIR" && python3 - <<'PY' ) >>"$LOG" 2>&1 && log "Pillow aus dem Internet geladen" || log "WARNUNG: Pillow fehlt – Artwork Manager braucht Internet beim nächsten Installieren"
import io, json, sys, urllib.request, zipfile
tag = "cp%d%d" % sys.version_info[:2]
info = json.load(urllib.request.urlopen("https://pypi.org/pypi/pillow/json", timeout=30))
url = next(f["url"] for f in info["urls"] if f"{tag}-{tag}-manylinux" in f["filename"] and "aarch64" in f["filename"])
zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(url, timeout=120).read())).extractall(".")
print("Pillow:", url.rsplit("/", 1)[1])
PY
    else
        log "Pillow bereits vorhanden"
    fi
fi

# --- PS1: funktionierenden Standard-Emulator sicherstellen ---
# Manche ROCKNIX-Versionen wählen pcsx_rearmed32, das nicht installiert ist (RetroArch bricht ab).
# Nur korrigieren, wenn kein Core gesetzt ist oder der gesetzte fehlt – eine gültige Wahl bleibt.
PSXCORE=$( ( . /etc/profile >/dev/null 2>&1; get_setting psx.core ) 2>/dev/null )
if [ -z "$PSXCORE" ] || [ ! -f "/usr/lib/libretro/${PSXCORE}_libretro.so" ]; then
    if [ -f /usr/lib/libretro/pcsx_rearmed_libretro.so ]; then
        ( . /etc/profile >/dev/null 2>&1; set_setting psx.emulator retroarch; set_setting psx.core pcsx_rearmed ) >/dev/null 2>&1
        log "PS1: Emulator auf pcsx_rearmed gesetzt (vorher: ${PSXCORE:-Standard})"
    fi
fi

# --- 3. Installer entfernen und auf Dual umschalten ---
rm -f "$PORTS/Install RDS.sh" "$PORTS/Install ROCKNIX DualStation.sh"
rm -rf "$SRC"
log "Installer-Dateien entfernt"

log "Umschalten auf Dual"
/bin/bash "$DEST/es-switch-helper.sh" dual
if [ -L "$OLDDEST" ]; then                     # ES läuft jetzt vom neuen Ort – Übergangs-Verweis weg
    rm -f "$OLDDEST" && log "Uebergangs-Verweis entfernt: $OLDDEST"
elif [ -d "$OLDDEST" ]; then
    log "WARNUNG: alter Programmordner $OLDDEST bleibt (neuer Ordner gab es schon) – die Deinstallation entfernt ihn"
fi
[ "$MODE" = update ] && log "=== Update fertig ($OLDVER -> $VERSION) ===" || log "=== Neuinstallation fertig ==="
exit 0
