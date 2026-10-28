#!/usr/bin/env python3
"""Baut die Installations-ZIP von RetroDualStation (RDS).

Aufruf (im Repo-Ordner):
    python3 tools/make-installer.py <ES-Binary> <version> [<canvas-ds-ZIP>]
                                    [--artwork <Artwork-Manager-Repo>] [--pillow <Pillow-Wheel>]
Mit canvas-ds-ZIP (aus tools/make-canvas-installer.py) wird canvas-ds mitinstalliert
und als Standard-Theme im Dual-Modus gesetzt.
--artwork: Ordner des RocknixDS-Artwork-Managers (Branch v5-foundation); dessen Paket
           rocknixds_artwork_manager kommt zusammen mit artworkmanager/ in den Ports-Ordner.
--pillow:  Pillow-Wheel für das Gerät (cp314, manylinux aarch64). Fehlt es, lädt der
           Installer Pillow auf dem Gerät selbst aus dem Internet.
Beispiel:
    python3 tools/make-installer.py emulationstation-rgds v9

Das Binary wird im Paket immer als "emulationstation-rgds" abgelegt
(ohne Versionsnummer); die Version steht nur in .dualstation/VERSION.

Ergebnis: retrodualstation-<version>.zip
Inhalt (wird in den Ordner "ports" auf der SD-Karte entpackt):
    Install RDS.sh
    .dualstation/   install.sh, VERSION, Binary, rds-install/, ports/, theme/, controlcenter/
"""
import os, sys, zipfile

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args, opts = [], {}
it = iter(sys.argv[1:])
for x in it:
    if x in ("--artwork", "--pillow"):
        opts[x] = next(it, None)
    else:
        args.append(x)
if len(args) not in (2, 3) or None in opts.values():
    sys.exit(__doc__)
binary, version = args[0], args[1]
canvas = args[2] if len(args) == 3 else None
if len(args) == 3 and not (canvas and os.path.isfile(canvas)):
    sys.exit("canvas-ZIP nicht gefunden: %r – erst tools/make-canvas-installer.py <version> ausführen" % canvas)
artwork_repo, pillow = opts.get("--artwork"), opts.get("--pillow")
binname = "emulationstation-rgds"

out = os.path.join(repo, f"retrodualstation-{version}.zip")
EXEC, FILE = 0o100755 << 16, 0o100644 << 16

def add(z, src, arc, mode):
    info = zipfile.ZipInfo.from_file(src, arc)
    info.external_attr = mode
    info.compress_type = zipfile.ZIP_DEFLATED
    with open(src, "rb") as f:
        z.writestr(info, f.read())

with zipfile.ZipFile(out, "w") as z:
    add(z, os.path.join(repo, "installer", "Install RDS.sh"), "Install RDS.sh", EXEC)
    p = ".dualstation/"
    add(z, os.path.join(repo, "installer", "payload", "install.sh"), p + "install.sh", EXEC)
    z.writestr(zipfile.ZipInfo(p + "VERSION"), version + "\n")
    import datetime
    z.writestr(zipfile.ZipInfo(p + "DATE"), datetime.date.today().strftime("%Y%m%d") + "\n")   # Release-Datum (Ports-Liste)
    add(z, binary, p + binname, EXEC)
    for f in ("start-es-dualstation.sh", "rgds-sway-fix.sh", "es-switch-helper.sh", "rgds-diag.sh", "rds-settings.py", "rds-migrate-savestates.py"):
        add(z, os.path.join(repo, "device", "rds-install", f), p + "rds-install/" + f, EXEC)
    add(z, os.path.join(repo, "installer", "payload", "uninstall.sh"), p + "rds-install/uninstall.sh", EXEC)
    for f in ("RDS Dual-Screen.sh", "RDS Single-Screen.sh"):
        add(z, os.path.join(repo, "device", "ports", f), p + "ports/" + f, EXEC)
    add(z, os.path.join(repo, "installer", "payload", "ports", "Uninstall RDS.sh"),
        p + "ports/Uninstall RDS.sh", EXEC)
    add(z, os.path.join(repo, "installer", "extras", "RDS Grid Info.sh"), p + "ports/RDS Grid Info.sh", EXEC)
    theme = os.path.join(repo, "theme", "dii-ess-aye-rds")
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
    add(z, os.path.join(repo, "installer", "payload", "drastic", "rds-microphone.wav"), p + "drastic/rds-microphone.wav", FILE)
    for f in sorted(os.listdir(os.path.join(repo, "installer", "payload", "images"))):
        add(z, os.path.join(repo, "installer", "payload", "images", f), p + "images/" + f, FILE)
    if canvas:   # canvas-ds aus dessen Installer-ZIP übernehmen
        with zipfile.ZipFile(canvas) as cz:
            pre = ".canvas-ds/canvas-rds/"
            for info in cz.infolist():
                if info.filename.startswith(pre) and not info.is_dir():
                    ni = zipfile.ZipInfo(p + "theme/canvas-rds/" + info.filename[len(pre):], info.date_time)
                    ni.external_attr, ni.compress_type = FILE, zipfile.ZIP_DEFLATED
                    z.writestr(ni, cz.read(info))
    # Artwork Manager (Gerätefassung): Programm, Ports-Eintrag, Manager-Paket, Pillow
    for f in ("rds_artwork.py", "multidisc.py"):
        add(z, os.path.join(repo, "artworkmanager", f), p + "artworkmanager/" + f, FILE)
    add(z, os.path.join(repo, "artworkmanager", "RDS Artwork Manager.sh"), p + "ports/RDS Artwork Manager.sh", EXEC)
    borders = os.path.join(repo, "artworkmanager", "borders")    # iiSU-Rahmen (tools/make-iisu-borders.py)
    for root, dirs, files in os.walk(borders):
        dirs.sort()
        for f in sorted(files):
            src = os.path.join(root, f)
            add(z, src, p + "artworkmanager/borders/" + os.path.relpath(src, borders), FILE)
    if artwork_repo:
        pkg = os.path.join(artwork_repo, "rocknixds_artwork_manager")
        if not os.path.isfile(os.path.join(pkg, "__init__.py")):
            sys.exit(f"Kein Artwork-Manager-Paket gefunden: {pkg}")
        for f in sorted(os.listdir(pkg)):
            if f.endswith(".py"):
                add(z, os.path.join(pkg, f), p + "artworkmanager/rocknixds_artwork_manager/" + f, FILE)
    else:
        print("Hinweis: ohne --artwork kommt das Artwork-Manager-Paket nicht mit")
    if pillow:
        add(z, pillow, p + "lib/pillow.whl", FILE)
    for f in ("LICENSE", "CREDITS.md"):
        add(z, os.path.join(repo, f), p + f, FILE)

print(out, os.path.getsize(out) // 1024, "KiB")
