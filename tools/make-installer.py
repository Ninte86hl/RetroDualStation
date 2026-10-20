#!/usr/bin/env python3
"""Baut die Installations-ZIP von ROCKNIX DualStation.

Aufruf (im Repo-Ordner):
    python3 tools/make-installer.py <ES-Binary> <version> [<canvas-ds-ZIP>]
Mit canvas-ds-ZIP (aus tools/make-canvas-installer.py) wird canvas-ds mitinstalliert
und als Standard-Theme im Dual-Modus gesetzt.
Beispiel:
    python3 tools/make-installer.py emulationstation-rgds v9

Das Binary wird im Paket immer als "emulationstation-rgds" abgelegt
(ohne Versionsnummer); die Version steht nur in .dualstation/VERSION.

Ergebnis: rocknix-dualstation-<version>.zip
Inhalt (wird in den Ordner "ports" auf der SD-Karte entpackt):
    Install ROCKNIX DualStation.sh
    .dualstation/   install.sh, VERSION, Binary, rgds-test/, ports/, theme/, controlcenter/
"""
import os, sys, zipfile

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) not in (3, 4):
    sys.exit(__doc__)
binary, version = sys.argv[1], sys.argv[2]
canvas = sys.argv[3] if len(sys.argv) == 4 else None
binname = "emulationstation-rgds"

out = os.path.join(repo, f"rocknix-dualstation-{version}.zip")
EXEC, FILE = 0o100755 << 16, 0o100644 << 16

def add(z, src, arc, mode):
    info = zipfile.ZipInfo.from_file(src, arc)
    info.external_attr = mode
    info.compress_type = zipfile.ZIP_DEFLATED
    with open(src, "rb") as f:
        z.writestr(info, f.read())

with zipfile.ZipFile(out, "w") as z:
    add(z, os.path.join(repo, "installer", "Install ROCKNIX DualStation.sh"), "Install ROCKNIX DualStation.sh", EXEC)
    p = ".dualstation/"
    add(z, os.path.join(repo, "installer", "payload", "install.sh"), p + "install.sh", EXEC)
    z.writestr(zipfile.ZipInfo(p + "VERSION"), version + "\n")
    add(z, binary, p + binname, EXEC)
    for f in ("start-es-dualstation.sh", "rgds-sway-fix.sh", "es-switch-helper.sh", "rgds-diag.sh"):
        add(z, os.path.join(repo, "device", "rgds-test", f), p + "rgds-test/" + f, EXEC)
    add(z, os.path.join(repo, "installer", "payload", "uninstall.sh"), p + "rgds-test/uninstall.sh", EXEC)
    for f in ("RGDS Dual-Screen ES.sh", "RGDS Single-Screen ES.sh"):
        add(z, os.path.join(repo, "device", "ports", f), p + "ports/" + f, EXEC)
    add(z, os.path.join(repo, "installer", "payload", "ports", "Uninstall ROCKNIX DualStation.sh"),
        p + "ports/Uninstall ROCKNIX DualStation.sh", EXEC)
    theme = os.path.join(repo, "theme", "dii-ess-aye-rgds-plus")
    for root, dirs, files in os.walk(theme):
        dirs.sort()
        for f in sorted(files):
            src = os.path.join(root, f)
            add(z, src, p + "theme/" + os.path.relpath(src, os.path.dirname(theme)), FILE)
    for f, mode in (("rds_cc.py", EXEC), ("rds-controlcenter.service", FILE),
                    ("rds-resume.service", FILE), ("rds-logind-powerkey.conf", FILE)):
        add(z, os.path.join(repo, "controlcenter", f), p + "controlcenter/" + f, mode)
    tour = os.path.join(repo, "controlcenter", "tour")      # Bilder der Tour
    for f in sorted(os.listdir(tour)):
        add(z, os.path.join(tour, f), p + "controlcenter/tour/" + f, FILE)
    for f in sorted(os.listdir(os.path.join(repo, "installer", "payload", "images"))):
        add(z, os.path.join(repo, "installer", "payload", "images", f), p + "images/" + f, FILE)
    if canvas:   # canvas-ds aus dessen Installer-ZIP übernehmen
        with zipfile.ZipFile(canvas) as cz:
            pre = ".canvas-ds/canvas-ds-rgds-plus/"
            for info in cz.infolist():
                if info.filename.startswith(pre) and not info.is_dir():
                    ni = zipfile.ZipInfo(p + "theme/canvas-ds-rgds-plus/" + info.filename[len(pre):], info.date_time)
                    ni.external_attr, ni.compress_type = FILE, zipfile.ZIP_DEFLATED
                    z.writestr(ni, cz.read(info))
    for f in ("LICENSE", "CREDITS.md"):
        add(z, os.path.join(repo, f), p + f, FILE)

print(out, os.path.getsize(out) // 1024, "KiB")
