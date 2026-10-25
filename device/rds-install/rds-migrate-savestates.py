#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""RetroDualStation: Savestates einmalig vom Schema bis v15.1 auf das Schema ab v15.2 umziehen.

Bis v15.1:  Nutzer-Plätze 0–8, Gameswitcher-Stand bei RetroArch auf Platz 9 (.state9), DraStic teilte Platz 0
            zwischen Nutzer und Gameswitcher, DSperate: Nutzer CODE.0–8.dss.
Ab v15.2:   Platz 0 = automatischer Stand (RetroArch .state, DraStic _0.dss, DSperate .auto.dss),
            Nutzer-Slots 1–9 = dieselben Nummern wie in den Emulatoren.

Umzug (nichts wird gelöscht, nie wird ein belegter Platz überschrieben):
  RetroArch  .state ↔ .state9 tauschen – alter Gameswitcher-Stand wird automatisch, alter Nutzer-Platz 0 wird Slot 9
  DSperate   CODE.0.dss → CODE.9.dss (sonst nächster freier Slot 1–9) – Platz 0 zeigt das Menü nicht mehr
  DraStic    _0.dss nach _9.dss kopieren, wenn frei – Platz 0 bleibt der automatische Stand
Vorschaubilder (*.png) ziehen jeweils mit.

  rds-migrate-savestates.py [--dry-run] [--fresh] [SAVESTATE-ORDNER]

--fresh (Neuinstallation, Stände stammen aus ROCKNIX ohne RDS): RetroArch .state in den nächsten freien Slot
         (9 abwärts) verschieben statt tauschen – ein vorhandener .state9 ist dann ein eigener Stand.

Nur EINMAL ausführen (der Installer setzt einen Merker) – ein zweiter Lauf würde RetroArch zurücktauschen.
"""
import os
import re
import shutil
import sys

ROOT = "/storage/roms/savestates"
DRY = False
FRESH = False
moves = []


def exists(p):
    return os.path.exists(p)


def mv(src, dst):
    for a, b in ((src, dst), (src + ".png", dst + ".png")):
        if exists(a) and not exists(b):
            moves.append("%s → %s" % (a, b))
            if not DRY:
                os.replace(a, b)


def cp(src, dst):
    for a, b in ((src, dst), (src + ".png", dst + ".png")):
        if exists(a) and not exists(b):
            moves.append("%s ⇒ %s (Kopie)" % (a, b))
            if not DRY:
                shutil.copy2(a, b)


def swap(a, b):
    """a und b tauschen (fehlt eine Seite, wird nur verschoben). Vorschaubilder mit."""
    tmp = a + ".rds-swap"
    for x, y in ((a, b), (a + ".png", b + ".png")):
        ex, ey = exists(x), exists(y)
        if not (ex or ey) or exists(x + ".rds-swap"):
            continue
        moves.append("%s ↔ %s" % (x, y))
        if DRY:
            continue
        if ex:
            os.replace(x, x + ".rds-swap")
        if ey:
            os.replace(y, x)
        if ex:
            os.replace(x + ".rds-swap", y)


def main(argv):
    global DRY, FRESH, ROOT
    DRY, FRESH = "--dry-run" in argv, "--fresh" in argv
    argv = [a for a in argv if a not in ("--dry-run", "--fresh")]
    if argv:
        ROOT = argv[0]
    if not os.path.isdir(ROOT):
        print("Keine Savestates gefunden (%s)" % ROOT)
        return 0
    for system in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, system)
        if not os.path.isdir(d):
            continue
        names = os.listdir(d)
        # RetroArch: <rom>.state9 (Gameswitcher bis v15.1) ↔ <rom>.state (Nutzer-Platz 0 bis v15.1)
        stems = {n[:-len(".state9")] for n in names if n.endswith(".state9")} | \
                {n[:-len(".state")] for n in names if n.endswith(".state")}
        for stem in sorted(stems):
            a, b = os.path.join(d, stem + ".state"), os.path.join(d, stem + ".state9")
            if FRESH:
                free = next((k for k in range(9, 0, -1) if not exists(os.path.join(d, "%s.state%d" % (stem, k)))), None)
                if exists(a) and free:
                    mv(a, os.path.join(d, "%s.state%d" % (stem, free)))
                elif exists(a):
                    print("RetroArch: kein freier Slot für %s – Platz 0 wird zum automatischen Stand" % a)
            else:
                swap(a, b)
        if system != "nds":
            continue
        # DSperate: CODE.0.dss → CODE.9.dss bzw. nächster freier Slot
        for n in sorted(names):
            m = re.fullmatch(r"([A-Z0-9]{4})\.0\.dss", n)
            if not m:
                continue
            free = next((k for k in (9, 8, 7, 6, 5, 4, 3, 2, 1)
                         if not exists(os.path.join(d, "%s.%d.dss" % (m.group(1), k)))), None)
            if free is None:
                print("DSperate: kein freier Slot für %s – bleibt liegen" % n)
                continue
            mv(os.path.join(d, n), os.path.join(d, "%s.%d.dss" % (m.group(1), free)))
        # DraStic: <rom>_0.dss bleibt automatisch, Kopie als Slot 9, wenn frei
        for n in sorted(names):
            if n.endswith("_0.dss"):
                cp(os.path.join(d, n), os.path.join(d, n[:-len("_0.dss")] + "_9.dss"))
    print(("Probelauf – " if DRY else "") + ("Savestates umgezogen: %d" % len(moves)))
    for line in moves:
        print("  " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
