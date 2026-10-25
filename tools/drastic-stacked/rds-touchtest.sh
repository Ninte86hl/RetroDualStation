#!/bin/bash
# Geführter Touch-Test für DraStic vertikal (Bildschirme übereinander). Mit Eingaben je Schritt.
# Aufruf vom PC:  ssh -t root@IP 'bash /storage/rds-stest/rds-touchtest.sh [TEIL-DES-ROM-NAMENS]'
# Ohne Angabe: Zelda Phantom Hourglass. Eine Touch-Test-ROM (zeigt die Stiftposition) ist ideal.
# Ablauf: hängt bei Bedarf ein, startet Zelda über ES, fragt sechs Tipps ab, schreibt alles nach ergebnis.txt.
D=/storage/rds-stest
LOG=$D/start.log
OUT=$D/ergebnis.txt
export SWAYSOCK=/run/0-runtime-dir/sway-ipc.0.sock

frage() {   # $1 = Text, setzt A
    read -r -p "$1 " A
}
neue_zeilen() {   # Touch-Zeilen seit Zeile $1
    grep "rds-touch" "$LOG" 2>/dev/null | tail -n +"$(( $1 + 1 ))"
}
zahl() { grep -c "rds-touch" "$LOG" 2>/dev/null || echo 0; }

echo "=== Touch-Test DraStic vertikal ($(date '+%d.%m. %H:%M')) ===" | tee "$OUT"
if ! grep -q " /usr/bin/start_drastic.sh " /proc/mounts; then
    if pidof drastic >/dev/null; then echo "DraStic läuft ohne Versuch – bitte beenden und neu aufrufen"; exit 1; fi
    sh $D/rds-stest.sh an || exit 1
fi
if ! pidof drastic >/dev/null; then
    ROM=$(ls /storage/roms/nds/* | grep -i -E "\.(nds|zip|7z)$" | grep -i -- "${1:-zelda.*phantom}" | head -1)
    [ -n "$ROM" ] || { echo "Keine ROM gefunden zu: ${1:-zelda.*phantom}"; ls /storage/roms/nds/ | grep -v -E "\.(dsv|sav)$" | head -40; exit 1; }
    echo "ROM: $(basename "$ROM")"
    frage "Jetzt starten? (j = automatisch über ES, n = ich starte es selbst)"
    if [ "$A" = "j" ]; then
        rm -f "$LOG"
        curl -s -X POST --data-binary "$ROM" http://127.0.0.1:1234/launch >/dev/null
    else
        echo "Bitte Zelda aus ES starten."
    fi
    for i in $(seq 1 120); do pidof drastic >/dev/null && break; sleep 0.5; done
    pidof drastic >/dev/null || { echo "DraStic startet nicht"; exit 1; }
fi
frage "Läuft das Spiel bzw. die Test-ROM und reagiert sie auf Touch (nicht im Intro)? Enter = weiter"

for P in "UNTEN links oben" "UNTEN rechts oben" "UNTEN links unten" "UNTEN rechts unten" "OBEN links oben" "OBEN rechts unten"; do
    N=$(zahl)
    frage ">>> Tippe einmal: $P – danach Enter"
    sleep 0.3
    Z=$(neue_zeilen "$N")
    [ -n "$Z" ] && echo "$Z" | sed 's/^/    /' || echo "    (kein Tipp bei DraStic angekommen)"
    frage "    Wo landete der Stift?  r = richtig · v = verschoben · n = nichts · o = auf dem oberen Bild"
    W=$A
    frage "    Bemerkung (Enter = keine):"
    echo "$P | Stift: $W | $A" >> "$OUT"
    [ -n "$Z" ] && echo "$Z" | sed 's/^/    /' >> "$OUT"
done

{
    echo "--- Stand ---"
    grep -E "Start|Bildschirm|DSHOOK|Touch auf" "$LOG"
    swaymsg -t get_outputs --raw | python3 -c 'import json,sys; [print(o["name"], o["rect"]) for o in json.load(sys.stdin)]'
    swaymsg -t get_inputs --raw | python3 -c 'import json,sys; [print(i["identifier"], i.get("libinput", {}).get("calibration_matrix", "")) for i in json.load(sys.stdin) if i["type"] == "touch"]'
} >> "$OUT" 2>&1
echo
echo "Fertig. Ergebnis schicken mit:  ssh root@$(hostname -i 2>/dev/null | cut -d' ' -f1) 'cat $OUT'"
echo "Spiel danach beenden und zurückstellen:  sh $D/rds-stest.sh aus"
