#!/bin/bash
# Hülle um das ROCKNIX-Startskript (nur im Versuch eingehängt): Bildschirme übereinander, DraStic vertikal,
# DSHOOK_WINDOW_SIZE für die neuere libdrastouch, Touch auf den unteren Bildschirm; danach alles zurück.
D=/storage/rds-stest
LOG=$D/start.log
export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock
C=/storage/.config/drastic/config/drastic.cfg
TOUCH="1046:911:Goodix_Capacitive_TouchScreen"
exec >"$LOG" 2>&1
echo "$(date +%T) Start: $*"
read -r W H <<<"$(swaymsg -t get_outputs --raw | python3 -c 'import json,sys; r=next(o["rect"] for o in json.load(sys.stdin) if o["name"]=="DSI-2"); print(r["width"], r["height"])')"
echo "Bildschirm oben: ${W}x${H}"
swaymsg "output DSI-2 position 0 0; output DSI-1 position 0 $H"
sed -i -E 's/^screen_orientation *= *.*/screen_orientation = 0/' "$C"
export DSHOOK_WINDOW_SIZE="${W}x$((H * 2))"
export RDS_TOUCH_DEBUG=1
echo "DSHOOK_WINDOW_SIZE=$DSHOOK_WINDOW_SIZE"
(   # nach dem Erscheinen des Fensters: Touch auf den unteren Bildschirm (die ROCKNIX-Regel setzt DSI-2)
    for i in $(seq 1 80); do swaymsg -t get_tree | grep -q '"app_id": "drastic"' && break; sleep 0.25; done
    for t in 0.5 1.5 3; do sleep $t; swaymsg "input \"$TOUCH\" map_to_output DSI-1" >/dev/null; done
    echo "$(date +%T) Touch auf DSI-1 (beide Goodix-Geräte haben dieselbe Kennung – Zuordnung gilt für beide)"
    swaymsg -t get_tree | grep -A3 '"app_id": "drastic"' | grep -E "rect|width|height" | head -4
) &
bash "$D/start_drastic.orig.sh" "$@" 2>&1 | while IFS= read -r l; do case "$l" in *ticks*) ;; *) echo "$l";; esac; done
RC=${PIPESTATUS[0]}
echo "$(date +%T) DraStic beendet ($RC)"
swaymsg "output DSI-2 position 0 0; output DSI-1 position $W 0"
sed -i -E 's/^screen_orientation *= *.*/screen_orientation = 1/' "$C"
exit $RC
