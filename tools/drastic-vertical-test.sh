#!/bin/sh
# Versuch: DraStic vertikal statt horizontal (Flackern/gleiches Bild mit „Follow 3D Renderer“).
# Nur vorübergehend – nichts davon bleibt nach „zurueck“ bzw. einem Neustart.
#
# Ablauf (auf dem Gerät, per SSH):
#   sh /storage/rds-vtest.sh vorbereiten [WERT]   in ES, DraStic beendet: drastic.cfg sichern, screen_orientation = WERT (Standard 0)
#   → Zelda aus ES starten (Follow 3D in den Spieleinstellungen an oder aus – je nach Test)
#   sh /storage/rds-vtest.sh an                    Spiel läuft: Bildschirme übereinander anordnen, DraStic neu einpassen
#   sh /storage/rds-vtest.sh aus                   Spiel läuft: wieder nebeneinander (wie ROCKNIX)
#   sh /storage/rds-vtest.sh zurueck               DraStic beendet: drastic.cfg und Anordnung wiederherstellen
#   sh /storage/rds-vtest.sh status                Anordnung und DraStic-Werte anzeigen
export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock
C=/storage/.config/drastic/config/drastic.cfg
B=/storage/rds-vtest-drastic.cfg
P=/storage/rds-vtest-outputs.txt
TOP=DSI-2
BOT=DSI-1

outputs() {   # Name x y Breite Höhe je Zeile
    swaymsg -t get_outputs --raw | python3 -c '
import json, sys
for o in json.load(sys.stdin):
    r = o["rect"]
    print(o["name"], r["x"], r["y"], r["width"], r["height"])'
}

restore_pos() {
    [ -f "$P" ] || { echo "Keine gemerkte Anordnung"; return; }
    cmd=""
    while read -r n x y w h; do cmd="$cmd output $n position $x $y;"; done < "$P"
    swaymsg "$cmd" >/dev/null
    swaymsg '[app_id="drastic"] fullscreen disable; [app_id="drastic"] fullscreen enable global' >/dev/null 2>&1
    echo "Anordnung wiederhergestellt"
}

case "$1" in
vorbereiten)
    pidof drastic >/dev/null && { echo "DraStic läuft – erst beenden"; exit 1; }
    [ -f "$B" ] || cp "$C" "$B"
    [ -f "$P" ] || outputs > "$P"
    sed -i -E "s/^screen_orientation *= *.*/screen_orientation = ${2:-0}/" "$C"
    echo "Gesichert: $B · Anordnung: $(tr '\n' ' ' < "$P")"
    grep -E "^screen_orientation|^fix_main_2d_screen|^screen_swap" "$C"
    ;;
an)
    [ -f "$P" ] || outputs > "$P"
    H=$(awk -v t="$TOP" '$1 == t {print $5}' "$P")
    [ -n "$H" ] || { echo "Bildschirm $TOP nicht gefunden"; exit 1; }
    swaymsg "output $TOP position 0 0; output $BOT position 0 $H" >/dev/null
    sleep 0.3
    swaymsg '[app_id="drastic"] fullscreen disable; [app_id="drastic"] fullscreen enable global' >/dev/null
    echo "Übereinander:"; outputs
    ;;
aus)
    restore_pos
    ;;
zurueck)
    pidof drastic >/dev/null && { echo "DraStic läuft – erst beenden"; exit 1; }
    restore_pos
    [ -f "$B" ] && cp "$B" "$C" && rm -f "$B" && echo "drastic.cfg wiederhergestellt"
    rm -f "$P"
    grep -E "^screen_orientation|^fix_main_2d_screen|^screen_swap" "$C"
    ;;
status|*)
    outputs
    grep -E "^screen_orientation|^fix_main_2d_screen|^screen_swap|^mirror_touch" "$C"
    grep -n "drastic" /storage/.config/sway/config
    ;;
esac
