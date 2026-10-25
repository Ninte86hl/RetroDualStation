#!/bin/bash
# RAM-Versuch: DSperate eingefroren im Speicher behalten, DraStic daneben spielen, DSperate wieder aufwecken.
# Nur zum Testen, gilt bis zum Neustart. Aufruf auf dem Gerät:  bash /storage/ramtest-ds.sh
# Vorher in ES ein Spiel mit DSperate starten. Ergebnis: /storage/ramtest-ds.log
LOG=/storage/ramtest-ds.log
export XDG_RUNTIME_DIR=/run/0-runtime-dir WAYLAND_DISPLAY=wayland-1 SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock
say() { echo "$(date +%H:%M:%S) $*" | tee -a "$LOG"; }
mem() { free -m | awk '/Mem:/{printf "RAM available %s MB", $7} /Swap:/{printf " · zram belegt %s MB", $3}'; }

: > "$LOG"
say "=== RAM-Versuch DSperate + DraStic ==="

# 1. zram (komprimierter Speicher) einschalten, falls noch nicht aktiv
if ! grep -q zram0 /proc/swaps; then
    modprobe zram 2>/dev/null
    cd /sys/block/zram0 || { say "FEHLER: kein zram"; exit 1; }
    grep -q lz4 comp_algorithm && echo lz4 > comp_algorithm
    echo 512M > disksize && mkswap /dev/zram0 >/dev/null && swapon -p 100 /dev/zram0
    echo 20 > /proc/sys/vm/swappiness
    cd /
fi
say "zram aktiv · $(mem)"

# 2. DSperate muss laufen
DSP=$(pidof dsperate)
[ -n "$DSP" ] || { say "FEHLER: DSperate läuft nicht – erst in ES ein DS-Spiel mit DSperate starten"; exit 1; }
say "DSperate läuft (PID $DSP, $(awk '/VmRSS/{print int($2/1024)" MB"}' /proc/$DSP/status)) · $(mem)"

# 3. DSperate samt Kindprozessen einfrieren
PIDS="$DSP $(pgrep -P $DSP | tr '\n' ' ')"
kill -STOP $PIDS
say "DSperate eingefroren · $(mem)"

# 4. Speicher alle 5 s mitschreiben, solange DraStic läuft
( while sleep 5; do say "  während DraStic: $(mem)"; done ) &
WATCH=$!

# 5. DraStic mit Zelda starten (an ES vorbei) – das Skript wartet, bis DraStic beendet wird
ROM=$(ls /storage/roms/nds/*Zelda*Phantom*.nds 2>/dev/null | head -1)
[ -n "$ROM" ] || ROM=$(ls /storage/roms/nds/*.nds | head -1)
say "Starte DraStic: $(basename "$ROM") – jetzt spielen, danach DraStic normal beenden"
/usr/bin/start_drastic.sh "$ROM" >/dev/null 2>&1
kill $WATCH 2>/dev/null
say "DraStic beendet · $(mem)"

# 6. DSperate aufwecken und Zeit messen
T0=$(date +%s%N)
kill -CONT $PIDS
sleep 2
T1=$(date +%s%N)
say "DSperate aufgeweckt (Signal + 2 s Wartezeit: $(( (T1 - T0) / 1000000 )) ms) · $(mem)"
dmesg | grep -iE "oom|killed process" | tail -3 | while read -r l; do say "WARNUNG: $l"; done
say "=== fertig – jetzt DSperate prüfen: Bild, Ton, Tasten, Touch ==="
