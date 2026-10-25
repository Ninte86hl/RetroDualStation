#!/bin/sh
# Versuch: DraStic mit übereinander angeordneten Bildschirmen (vertikal) – Touch über die neuere libdrastouch.
# Alles nur bis zum Neustart (Bind-Mounts), nichts im System wird dauerhaft geändert.
#   sh /storage/rds-stest/rds-stest.sh an       in ES, DraStic beendet: neue libdrastouch + Start-Hülle einhängen
#   → Zelda normal aus ES starten
#   sh /storage/rds-stest/rds-stest.sh aus      DraStic beendet: alles aushängen, Anordnung und drastic.cfg zurück
#   sh /storage/rds-stest/rds-stest.sh status
D=/storage/rds-stest
export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock
C=/storage/.config/drastic/config/drastic.cfg
case "$1" in
an)
    pidof drastic >/dev/null && { echo "DraStic läuft – erst beenden"; exit 1; }
    [ -s "$C" ] || { echo "drastic.cfg leer – abbrechen"; exit 1; }
    grep -q " /usr/bin/start_drastic.sh " /proc/mounts && { echo "Schon eingehängt"; exit 0; }
    [ -s "$D/drastic.cfg.vorher" ] || cp "$C" "$D/drastic.cfg.vorher"
    cp /usr/bin/start_drastic.sh "$D/start_drastic.orig.sh"
    chmod +x "$D/start_drastic.orig.sh" "$D/rds-start-drastic.sh"
    mount --bind "$D/libdrastouch.so" /usr/lib/libdrastouch.so &&
    mount --bind "$D/rds-start-drastic.sh" /usr/bin/start_drastic.sh && echo "Eingehängt – jetzt Zelda aus ES starten"
    ;;
aus)
    pidof drastic >/dev/null && { echo "DraStic läuft – erst beenden"; exit 1; }
    umount /usr/bin/start_drastic.sh 2>/dev/null; umount /usr/lib/libdrastouch.so 2>/dev/null
    W=$(swaymsg -t get_outputs --raw | python3 -c 'import json,sys; print(next(o["rect"]["width"] for o in json.load(sys.stdin) if o["name"]=="DSI-2"))')
    swaymsg "output DSI-2 position 0 0; output DSI-1 position $W 0" >/dev/null
    [ -s "$D/drastic.cfg.vorher" ] && cp "$D/drastic.cfg.vorher" "$C" && rm -f "$D/drastic.cfg.vorher" && echo "drastic.cfg zurück"
    grep -c "drastic" /proc/mounts | sed 's/^/Bind-Mounts übrig: /'
    ;;
*)
    grep "drastouch\|start_drastic" /proc/mounts
    swaymsg -t get_outputs --raw | python3 -c 'import json,sys; [print(o["name"], o["rect"]) for o in json.load(sys.stdin)]'
    grep -E "^screen_orientation|^threaded_3d|^fix_main" "$C"
    tail -15 $D/start.log 2>/dev/null
    ;;
esac
