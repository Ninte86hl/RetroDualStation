#!/bin/bash
# RDS – Deinstallation
# Aufruf: systemd-run --no-block /bin/bash /storage/rds-install/uninstall.sh
# Schaltet auf das Original-ROCKNIX-ES zurueck und entfernt alle Dateien
# von RDS. Spiele, Medien und Gamelists bleiben unberuehrt.

DEST=/storage/rds-install
[ -d "$DEST" ] || DEST=/storage/rgds-test       # Name bis v15.1
PORTS=/storage/roms/ports
THEMEDIR=/storage/.config/emulationstation/themes
LOG=/storage/dualstation-uninstall.log

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

log "=== Deinstallation RDS $(cat $DEST/VERSION 2>/dev/null) ==="

# Absicherung: Merker bis die Einstellungen zurückgesetzt sind. Bricht die Deinstallation vorher ab (Akku leer,
# Absturz), stellt rds-uninstall-guard.service beim nächsten Start die Notfall-Sicherung wieder her.
MARK=/storage/.config/rds-uninstall.running
RDSZIP=/storage/roms/backup/RDS_ORIGINAL_BACKUP.zip
RDSZIPI=/storage/.config/rds-backup/RDS_ORIGINAL_BACKUP.zip      # interne Kopie (immer erreichbar)
touch "$MARK"
zip_restore() {   # wie ROCKNIX' „backuptool restore“, aber mit unserer ZIP (ROCKNIX_BACKUP.zip bleibt unberührt)
    local z="$RDSZIPI"
    [ -f "$z" ] || z="$RDSZIP"
    [ -f "$z" ] || { log "FEHLER: keine Notfall-Sicherung ($RDSZIPI, $RDSZIP)"; return 1; }
    unzip -o "$z" -d / >>"$LOG" 2>&1 && log "Notfall-Sicherung wiederhergestellt: $z"
}

# Ports-Eintraege vor dem ES-Neustart entfernen, damit ES sie nicht mehr anzeigt
for f in "RDS Dual-Screen.sh" "RDS Single-Screen.sh" "Uninstall RDS.sh" "Install RDS.sh" "Artwork Manager.sh" \
         "RGDS Dual-Screen ES.sh" "RGDS Single-Screen ES.sh" "Uninstall ROCKNIX DualStation.sh"; do   # alte Namen bis v13.1
    rm -f "$PORTS/$f" && log "entfernt: $PORTS/$f"
done

# Originalwerte von vor RDS zurücksetzen (RetroArch, DraStic, DSperate, ES-Einstellungen, ES-Tastenbelegung).
# ES vorher anhalten, damit es seine Einstellungen nicht beim Beenden zurückschreibt; der Helfer startet es danach.
systemctl stop essway
RACFG=/storage/.config/retroarch/retroarch.cfg
DCFG=/storage/.config/drastic/config/drastic.cfg
DSPINI=/storage/.config/dsperate/dsperate.ini
ESINPUT=/storage/.emulationstation/es_input.cfg
if [ -f "$DEST/settings-before-rds.json" ] && [ -f "$DEST/rds-settings.py" ]; then
    if python3 "$DEST/rds-settings.py" restore "$DEST/settings-before-rds.json" >>"$LOG" 2>&1; then
        rm -f "$RACFG.vor-rds-kuerzel" "$DSPINI.vor-rds-kuerzel" "$DCFG.vor-rds-kuerzel" "$ESINPUT.before-rds"
        log "Originalwerte zurueckgesetzt, alte Sicherungen entfernt"
        rm -f "$MARK"
    else
        log "WARNUNG: Zuruecksetzen unvollstaendig – Notfall-Sicherung wird wiederhergestellt"
        zip_restore && rm -f "$MARK"
    fi
elif [ -f "$RDSZIPI" ] || [ -f "$RDSZIP" ]; then
    log "Sicherung der Originalwerte fehlt – Notfall-Sicherung wird wiederhergestellt"
    zip_restore && rm -f "$MARK"
else
    log "Keine Sicherung der Originalwerte gefunden (Installation vor v15.2) – Einstellungen bleiben"
    rm -f "$MARK"
fi
[ -f "$MARK" ] && log "WARNUNG: Einstellungen nicht zurueckgesetzt – Merker bleibt, Wiederherstellung beim naechsten Start"
sed -i '/for_window \[app_id="^emulationstation-rgds"\] fullscreen enable global/d' /storage/.config/sway/config 2>/dev/null

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

# Icons und gamelist-Einträge entfernen
rm -f "$PORTS"/images/rds-dual.png "$PORTS"/images/rds-single.png "$PORTS"/images/rds-uninstall.png "$PORTS"/images/rds-install.png "$PORTS"/images/rds-artwork.png
# Artwork Manager: Programm entfernen, Daten (settings.cfg, Sicherungen) bleiben im Ordner
AMDIR="$PORTS/artworkmanager"
rm -rf "$AMDIR/rocknixds_artwork_manager" "$AMDIR/__pycache__" "$AMDIR/rds_artwork.py" "$AMDIR/multidisc.py" "$AMDIR/manager.log"
rmdir "$AMDIR" 2>/dev/null && log "entfernt: $AMDIR" || log "Artwork-Manager-Daten bleiben: $AMDIR"
[ -f "$PORTS/gamelist.xml" ] && python3 - "$PORTS/gamelist.xml" <<'PY' 2>>"$LOG"
import sys, xml.etree.ElementTree as ET
f = sys.argv[1]
tree = ET.parse(f); root = tree.getroot()
drop = {"./RDS Dual-Screen.sh", "./RDS Single-Screen.sh", "./Uninstall RDS.sh", "./Install RDS.sh", "./Artwork Manager.sh",
        "./RGDS Dual-Screen ES.sh", "./RGDS Single-Screen ES.sh", "./Uninstall ROCKNIX DualStation.sh", "./Install ROCKNIX DualStation.sh"}
for g in [g for g in root.findall("game") if g.findtext("path") in drop]:
    root.remove(g)
tree.write(f, encoding="utf-8", xml_declaration=True)
PY

# Kontrollcenter und Geräteeinstellungen
SYSD=/storage/.config/system.d
systemctl stop rds-controlcenter 2>/dev/null
rm -f "$SYSD/essway.service.wants/rds-controlcenter.service" "$SYSD/rds-controlcenter.service" \
      "$SYSD"/*.target.wants/rds-resume.service "$SYSD/rds-resume.service" \
      /storage/.config/logind.conf.d/rds-logind-powerkey.conf
[ -f "$MARK" ] || rm -f "$SYSD/multi-user.target.wants/rds-uninstall-guard.service" "$SYSD/rds-uninstall-guard.service"
for w in essway.service suspend.target hibernate.target hybrid-sleep.target multi-user.target; do
    rmdir "$SYSD/$w.wants" 2>/dev/null                     # nur wenn leer (eigene Dienste anderer bleiben)
done
SS="$(cat /storage/.config/retrodualstation/savestates.done 2>/dev/null)"   # vor dem Löschen merken
AH="$(cat /storage/.config/retrodualstation/autohotkeys.done 2>/dev/null)"
rm -rf /storage/.config/retrodualstation /storage/.config/rds-controlcenter
systemctl daemon-reload
systemctl kill -s HUP systemd-logind 2>/dev/null
RA="$(cat "$DEST/retroachievements.before" 2>/dev/null)"
[ -n "$RA" ] && ( . /etc/profile >/dev/null 2>&1; set_setting global.retroachievements "$RA" ) >/dev/null 2>&1
BS="$(cat "$DEST/bottomscreen.before" 2>/dev/null)"
( . /etc/profile >/dev/null 2>&1; [ "$BS" = none ] && BS=vc; set_setting rocknix.bottomscreen.type "${BS:-vc}" ) >/dev/null 2>&1
[ -n "$SS" ] && ( . /etc/profile >/dev/null 2>&1; set_setting global.savestates "$SS" ) >/dev/null 2>&1
[ -n "$AH" ] && ( . /etc/profile >/dev/null 2>&1; set_setting system.autohotkeys "$AH" ) >/dev/null 2>&1
sed -i '/RetroDualStation: gptokeyb/d; /4660:22136:Fake_Keyboard/d; /RetroDualStation: virtuelle Tasten/d; /21060:21297:RDS_Keys/d' /storage/.config/sway/config 2>/dev/null
sed -i '/^# RetroDualStation$/,/^invisible=1$/d' /storage/.config/mako/config 2>/dev/null
log "Kontrollcenter und Geraeteeinstellungen entfernt"

rm -rf "$THEMEDIR/dii-ess-aye-rds" "$THEMEDIR/dii-ess-aye-rgds-plus" && log "entfernt: Theme dii-ess-aye-rds"
rm -f /storage/.config/emulationstation/themesettings/dii-ess-aye-rds.cfg \
      /storage/.config/emulationstation/themesettings/dii-ess-aye-rgds-plus.cfg
rm -rf "$THEMEDIR/canvas-ds-rgds-plus" /storage/.config/emulationstation/themesettings/canvas-ds-rgds-plus.cfg   # Namen bis v13.1
if [ -d "$THEMEDIR/canvas-rds" ]; then
    rm -rf "$THEMEDIR/canvas-rds" /storage/.config/emulationstation/themesettings/canvas-rds.cfg
    log "entfernt: Theme canvas-rds"
fi
rm -f /storage/dualstation-canvas-install.log
rm -rf "$DEST" /storage/rds-install /storage/rgds-test && log "entfernt: $DEST"
rm -f /storage/dualstation-install.log && log "entfernt: /storage/dualstation-install.log"

# Restliche Dateien von RDS. Bleiben immer: Spiele, Artworks, Savestates, Spielstände, Screenshots,
# die Daten des Artwork Managers (Einstellungen, Bildsicherungen) und dieses Log.
# Slot-Vorschaubilder von DraStic/DSperate (*.dss.png) legt nur RDS an – die Vorschaubilder von RetroArch
# (*.state*.png) erzeugt RetroArch selbst und bleiben. Eine liegengebliebene DraStic-Zwischenkopie (*.rdsbak,
# nur nach einem Absturz mitten im Speichern) ist der echte Stand des Platzes – zurück an ihren Platz.
SSDIR=/storage/roms/savestates
if [ -d "$SSDIR" ]; then
    find "$SSDIR" -type f \( -name '*.dss.png' -o -name '*.dss.png.tmp' \) -delete
    find "$SSDIR" -type f -name '*.rdsbak' | while read -r f; do mv -f "$f" "${f%.rdsbak}"; done
    log "entfernt: Slot-Vorschaubilder von RDS"
fi
rm -rf "$PORTS/.dualstation"                                    # Reste eines abgebrochenen Installers
rm -f /storage/logs/rds-report-*.tar.gz                         # Fehlerberichte des Kontrollcenters
rm -rf /storage/thumbnails/cheevos/badges                       # Zwischenspeicher der Erfolgs-Symbole (lädt bei Bedarf neu)
rmdir /storage/thumbnails/cheevos /storage/thumbnails 2>/dev/null
if [ -f "$MARK" ]; then
    log "Notfall-Sicherung bleibt (Einstellungen nicht zurueckgesetzt): $RDSZIP"
else
    rm -f "$RDSZIP" "${RDSZIP%.zip}.txt" "$RDSZIPI" && log "entfernt: Notfall-Sicherung (nicht mehr noetig)"
    rmdir "${RDSZIPI%/*}" 2>/dev/null
fi
log "=== Deinstallation fertig ==="
exit 0
