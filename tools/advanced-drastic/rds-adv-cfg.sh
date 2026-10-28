#!/bin/bash
# drastic.cfg nach advanced_drastic aufräumen – geführt, mit Rückfrage.
# advanced_drastic hat drastic.cfg umgeschrieben: eigene Zeilen (layout_index, ADVANCE_CONTROL_INDEX_…, HOT_…),
# SWAP_ORIENTATION ersetzt, Einstellungen geändert (hires_3d, frameskip_type, firmware.username → „Dr DraStic“).
# Neu aufgebaut wird die Datei aus der Fassung vor advanced (/storage/.config/drastic.tar.gz); übernommen werden nur
# die Tastenbelegungen (controls_a/b) und die RDS-Einstellungen (savestate_number, compress_savestates, screen_swap)
# von heute, weil RDS dort seitdem Werte gesetzt hat (z. B. Beenden = F7).
# Aufruf vom PC:  ssh -t root@IP 'bash /storage/rds-adv-cfg.sh'
B=/storage/.config/drastic.tar.gz
C=/storage/.config/drastic/config/drastic.cfg
pidof drastic drastic_v2522 >/dev/null && { echo "DraStic läuft – bitte erst das Spiel beenden."; exit 1; }
[ -f "$B" ] && [ -f "$C" ] || { echo "Sicherung oder drastic.cfg fehlt – nichts geändert."; exit 1; }
rm -rf /tmp/rds-cfg && mkdir -p /tmp/rds-cfg && tar xzf "$B" -C /tmp/rds-cfg drastic/config/drastic.cfg || exit 1
python3 - /tmp/rds-cfg/drastic/config/drastic.cfg "$C" /tmp/rds-cfg/neu.cfg <<'PY'
import sys
old_p, cur_p, out_p = sys.argv[1:4]
RDS_KEYS = ("savestate_number", "compress_savestates", "screen_swap")   # setzt der RDS-Installer
def parse(p):
    out = []
    for line in open(p):
        k, sep, v = line.rstrip("\n").partition(" = ")
        out.append((k, v) if sep else (line.rstrip("\n"), None))
    return out
old, cur = parse(old_p), dict((k, v) for k, v in parse(cur_p) if v is not None)
res, changes = [], []
for k, v in old:
    if v is None:
        res.append(k)
        continue
    nv = v
    if (k.startswith("controls_") or k in RDS_KEYS) and k in cur and cur[k] != v:
        nv = cur[k]                                   # Tastenbelegung/RDS-Einstellung von heute
        changes.append("  übernommen: %s = %s (vorher %s)" % (k, nv, v))
    elif k in cur and cur[k] != v:
        changes.append("  zurück:     %s = %s (advanced hatte %s)" % (k, v, cur[k]))
    res.append("%s = %s" % (k, nv))
dropped = [k for k in cur if k not in dict((k, v) for k, v in old if v is not None)]
open(out_p, "w").write("\n".join(res) + "\n")
print("\n".join(changes) or "  (keine Wertänderungen)")
print("  entfernt (nur advanced): %d Zeilen – %s" % (len(dropped), ", ".join(dropped[:6]) + (" …" if len(dropped) > 6 else "")))
PY
read -r -p ">>> drastic.cfg so neu schreiben? (j = ja) " A < /dev/tty
[ "$A" = "j" ] || { echo "Abgebrochen – nichts geändert."; exit 0; }
cp "$C" "$C.rds-advanced-$(date +%Y%m%d-%H%M)" && cp /tmp/rds-cfg/neu.cfg "$C" && echo "Fertig. Alte Fassung: $C.rds-advanced-*"
