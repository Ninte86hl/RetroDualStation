#!/bin/bash
# Zurück von advanced_drastic (trngaje) zum ROCKNIX-DraStic – geführt, mit Rückfrage.
# Aufruf vom PC:  ssh -t root@IP 'bash /storage/rds-adv-zurueck.sh'
#
# Anders als trngajes uninstall-Skript (löscht /storage/.config/drastic komplett und packt die Sicherung vom
# Installationstag aus) bleibt hier alles erhalten, was seitdem dazukam: drastic.cfg (RDS-Kürzel, Beenden F7 …),
# Spielstände/Savestates, BIOS, das RDS-Pust-Geräusch. Entfernt werden nur Dateien, die es in der Sicherung nicht gab
# (drastic_v25xx, libs, resources …), und Programmdateien aus der Sicherung zurückgeholt (Starter „drastic“).
# Vorher wird der aktuelle Stand komplett gesichert: /storage/rds-drastic-advanced-<Datum>.tar.gz
B=/storage/.config/drastic.tar.gz
D=/storage/.config/drastic
STAMP=$(date +%Y%m%d-%H%M)
SAFE=/storage/rds-drastic-advanced-$STAMP.tar.gz

pidof drastic drastic_v2522 drastic_v2520 >/dev/null && { echo "DraStic läuft – bitte erst das Spiel beenden."; exit 1; }
[ -f "$B" ] || { echo "Sicherung $B fehlt – nichts geändert."; exit 1; }
[ -d "$D" ] || { echo "$D fehlt – nichts geändert."; exit 1; }
[ -e "$D/drastic_v2522" ] || [ -e "$D/drastic_v2520" ] || echo "Hinweis: kein drastic_v25xx gefunden – advanced_drastic evtl. schon entfernt."

python3 - "$B" "$D" <<'PY'
import hashlib, os, sys, tarfile
backup, d = sys.argv[1], sys.argv[2]
KEEP = ("config/", "savestates", "backup", "cheats", "system/", "microphone/")   # Nutzerdaten/RDS: nie anfassen
t = tarfile.open(backup)
inb = {}
for m in t.getmembers():
    if m.name == "drastic" or m.name.startswith("drastic/"):
        inb[m.name[len("drastic/"):] if m.name != "drastic" else ""] = m
cur = set()
for root, dirs, files in os.walk(d):
    rel = os.path.relpath(root, d)
    rel = "" if rel == "." else rel + "/"
    for x in dirs + files:
        cur.add(rel + x)
extra = sorted(p for p in cur if p not in inb and not p.startswith(KEEP)
               and not any(p.startswith(q + "/") for q in cur if os.path.islink(os.path.join(d, q))))
ex = set(extra)
top = sorted(p for p in extra if os.path.dirname(p) not in ex)   # oberste neue Einträge (Inhalt geht mit)
restore = []
for name, m in inb.items():
    if not name or not m.isfile() or name.startswith(KEEP):
        continue
    path = os.path.join(d, name)
    data = t.extractfile(m).read()
    if not os.path.isfile(path) or open(path, "rb").read() != data:
        restore.append(name)
print("Sicherung vom Installationstag:", backup)
print("Wird entfernt (gab es vorher nicht):", ", ".join(top) or "nichts")
print("Wird aus der Sicherung zurückgeholt:", ", ".join(restore) or "nichts")
print("Bleibt unverändert: drastic.cfg, Savestates/Spielstände, BIOS, Mikrofon-Geräusch")
open("/tmp/rds-adv-plan.txt", "w").write("\n".join(["X " + p for p in top] + ["R " + p for p in restore]) + "\n")
PY
[ -s /tmp/rds-adv-plan.txt ] || exit 1
read -r -p ">>> So zurückbauen? (j = ja) " A < /dev/tty
[ "$A" = "j" ] || { echo "Abgebrochen – nichts geändert."; exit 0; }

echo "Sichere den aktuellen Stand nach $SAFE …"
tar czf "$SAFE" -C /storage/.config drastic || { echo "Sicherung fehlgeschlagen – nichts geändert."; exit 1; }
python3 - "$B" "$D" <<'PY'
import os, shutil, sys, tarfile
backup, d = sys.argv[1], sys.argv[2]
t = tarfile.open(backup)
for line in open("/tmp/rds-adv-plan.txt"):
    kind, name = line.rstrip("\n").split(" ", 1)
    path = os.path.join(d, name)
    if kind == "X":
        if os.path.islink(path) or os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        print("entfernt:", name)
    else:
        m = t.getmember("drastic/" + name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(t.extractfile(m).read())
        os.chmod(path, m.mode)
        print("zurückgeholt:", name)
PY
rm -f /tmp/rds-adv-plan.txt
echo
echo "Fertig. ROCKNIX-DraStic ist wieder aktiv:"
ls -l "$D/drastic" "$D/microphone/microphone.wav" 2>/dev/null
md5sum "$D/microphone/microphone.wav" 2>/dev/null | grep -q ddc2dc599fb6bba82d8c69eb9468f0df \
    && echo "Mikrofon: RDS-Pust-Geräusch ✓" || echo "Mikrofon: NICHT das RDS-Geräusch – RDS neu installieren oder melden"
echo "Sicherung des advanced-Stands: $SAFE (kann gelöscht werden, wenn alles läuft)"
