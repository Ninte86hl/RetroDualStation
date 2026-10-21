#!/bin/bash
# ROCKNIX DualStation – Installation
# Aufruf: systemd-run --no-block /bin/bash <ports>/.dualstation/install.sh <ports>
#
# 1. Pruefen: RG DS Plus oder RG DS (DSI-1 + DSI-2 gleich gross), ES-Binary laeuft auf
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
BIN=emulationstation-rgds

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
# Dateien aelterer Versionen (mit Versionsnummer im Namen) entfernen
for old in "$DEST"/emulationstation-rgds-* "$DEST"/start-es-v2-diag.sh; do
    [ -f "$old" ] && rm -f "$old" && log "entfernt: $old"
done

for f in start-es-dualstation.sh rgds-sway-fix.sh es-switch-helper.sh rgds-diag.sh uninstall.sh; do
    cp "$SRC/rgds-test/$f" "$DEST/$f" || fail "Could not copy $f."
    chmod +x "$DEST/$f"
done
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

# canvas-ds (Standard-Theme im Dual-Modus, falls im Paket)
if [ -d "$SRC/theme/canvas-ds-rgds-plus" ]; then
    rm -rf "$THEMEDIR/canvas-ds-rgds-plus.new"
    mv "$SRC/theme/canvas-ds-rgds-plus" "$THEMEDIR/canvas-ds-rgds-plus.new" || fail "Could not copy canvas-ds (not enough space?)."
    rm -rf "$THEMEDIR/canvas-ds-rgds-plus"
    mv "$THEMEDIR/canvas-ds-rgds-plus.new" "$THEMEDIR/canvas-ds-rgds-plus"
    [ -f "$DEST/theme.dual" ] || echo canvas-ds-rgds-plus > "$DEST/theme.dual"
    log "Theme kopiert: canvas-ds-rgds-plus (Standard im Dual-Modus: $(cat "$DEST/theme.dual"))"
fi

# Icons für die Ports-Einträge (gamelist.xml ergänzen, vorhandene Einträge bleiben)
if [ -d "$SRC/images" ]; then
    mkdir -p "$PORTS/images"
    cp "$SRC"/images/rds-*.png "$PORTS/images/"
    python3 - "$PORTS/gamelist.xml" <<'PY' 2>>"$LOG"
import os, sys, xml.etree.ElementTree as ET
f = sys.argv[1]
root = ET.parse(f).getroot() if os.path.exists(f) and os.path.getsize(f) else ET.Element("gameList")
entries = {"RGDS Dual-Screen ES.sh": ("Dual-Screen ES", "rds-dual.png"),
           "RGDS Single-Screen ES.sh": ("Single-Screen ES", "rds-single.png"),
           "Uninstall ROCKNIX DualStation.sh": ("Uninstall ROCKNIX DualStation", "rds-uninstall.png"),
           "Artwork Manager.sh": ("Artwork Manager", "rds-artwork.png")}
for script, (name, img) in entries.items():
    path = "./" + script
    g = next((g for g in root.findall("game") if g.findtext("path") == path), None)
    if g is None:
        g = ET.SubElement(root, "game")
        ET.SubElement(g, "path").text = path
    for tag, val in (("name", name), ("image", "./images/" + img), ("thumbnail", "./images/" + img)):
        e = g.find(tag)
        if e is None:
            e = ET.SubElement(g, tag)
        e.text = val
ET.indent(root)
ET.ElementTree(root).write(f, encoding="utf-8", xml_declaration=True)
PY
    log "Icons fuer Ports-Eintraege gesetzt"
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

    # RetroArch: keine Rückfragen bei Neustart/Beenden, keine Speicherstand-Einblendung (Gameswitcher)
    RACFG=/storage/.config/retroarch/retroarch.cfg
    if [ -f "$RACFG" ] && ! pidof retroarch >/dev/null; then
        sed -i -e 's/^confirm_reset = .*/confirm_reset = "false"/' \
               -e 's/^confirm_close = .*/confirm_close = "false"/' \
               -e 's/^notification_show_save_state = .*/notification_show_save_state = "false"/' \
               -e 's/^video_font_enable = .*/video_font_enable = "false"/' \
               -e 's/^menu_enable_widgets = .*/menu_enable_widgets = "false"/' "$RACFG"
        # Netzbefehle (Port 55355, nur lokal genutzt): Kontrollcenter/Gameswitcher speichern, laden
        # und beenden darüber – bei frischem ROCKNIX sind sie aus
        for kv in 'network_cmd_enable=true' 'quit_press_twice=false'; do
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
    # DraStic: Menü und Vorspulen auf Tasten, die das RG DS Plus nicht hat (R3 und den fehlenden rechten Stick)
    # → nur über das Kontrollcenter erreichbar, L3 bleibt frei. Einmalig, mit Sicherung.
    # Nur RG DS Plus: das RG DS hat R3 und den rechten Stick – dort bleibt die ROCKNIX-Belegung
    # (Menü L3, Vorspulen R3); das Kontrollcenter liest die Belegung aus drastic.cfg.
    DMARK=/storage/.config/retrodualstation/drastic-kuerzel.done
    DCFG=/storage/.config/drastic/config/drastic.cfg
    if [ "$DEVICE" = "RG DS Plus" ] && [ ! -f "$DMARK" ] && [ -f "$DCFG" ] && ! pidof drastic >/dev/null; then
        cp "$DCFG" "$DCFG.vor-rds-kuerzel"
        sed -i -E -e 's/^(controls_[ab]\[CONTROL_INDEX_MENU\]) = .*/\1 = 1036/' \
                  -e 's/^(controls_[ab]\[CONTROL_INDEX_FAST_FORWARD\]) = .*/\1 = 1154/' "$DCFG"
        date > "$DMARK"
        log "DraStic: Menue auf R3, Vorspulen auf rechten Stick (nur ueber das CC)"
    fi
    # ES-Savestate-Manager aus: Speicherplätze verwaltet das Kontrollcenter (einmalig, alter Wert gemerkt)
    SSMARK=/storage/.config/retrodualstation/savestates.done
    if [ ! -f "$SSMARK" ]; then
        SSOLD="$( . /etc/profile >/dev/null 2>&1; get_setting global.savestates )"
        ( . /etc/profile >/dev/null 2>&1; set_setting global.savestates auto ) >/dev/null 2>&1
        echo "$SSOLD" > "$SSMARK"
        log "ES: Savestate-Manager aus (vorher: ${SSOLD:-Standard})"
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
rm -f "$PORTS/Install ROCKNIX DualStation.sh"
rm -rf "$SRC"
log "Installer-Dateien entfernt"

log "Umschalten auf Dual"
/bin/bash "$DEST/es-switch-helper.sh" dual
log "=== Installation fertig ==="
exit 0
