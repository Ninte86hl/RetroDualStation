#!/usr/bin/env python3
"""RocknixDS Artwork Manager (Repo RocknixDS-v5): RDS an beiden Programmordnern erkennen.

RDS heißt auf dem Gerät seit v15.2 /storage/rds-install (bis v15.1 /storage/rgds-test). Das Paket erkannte RDS nur
an /storage/rgds-test/es-switch-helper.sh und brach sonst mit „Nicht unterstützte Firmware“ ab. Dieses Skript ändert
rocknixds_artwork_manager/device.py so, dass die Prüfung auf dem Gerät (Shell, auch über SSH) beide Pfade testet.

Aufruf (am PC):
    python3 tools/patch-rocknixds-marker.py ~/Desktop/RocknixDS-v5            # ändern, Unterschied zeigen
    python3 tools/patch-rocknixds-marker.py ~/Desktop/RocknixDS-v5 --commit   # zusätzlich committen
    python3 tools/patch-rocknixds-marker.py ~/Desktop/RocknixDS-v5 --check    # nur prüfen, nichts ändern
Mehrfach ausführen ist unschädlich (bereits angepasst → nichts zu tun).
"""
import difflib
import py_compile
import subprocess
import sys
from pathlib import Path

OLD_CONST = 'DUALSTATION_MARKER="/storage/rgds-test/es-switch-helper.sh"'
NEW_CONST = ('DUALSTATION_MARKER="/storage/rds-install/es-switch-helper.sh"\n'
             '# RDS-Programmordner: seit RDS v15.2 rds-install, bis v15.1 rgds-test – beide erkennen\n'
             'DUALSTATION_MARKERS=("/storage/rds-install/es-switch-helper.sh","/storage/rgds-test/es-switch-helper.sh")')
OLD_TEST = "if [ -e {shlex.quote(DUALSTATION_MARKER)} ]; then printf yes; else printf no; fi; "
NEW_TEST = ("if {' || '.join('[ -e '+shlex.quote(m)+' ]' for m in dict.fromkeys((DUALSTATION_MARKER,)+DUALSTATION_MARKERS))}; "
            "then printf yes; else printf no; fi; ")


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    commit, check = "--commit" in argv, "--check" in argv
    if len(args) != 1:
        sys.exit(__doc__)
    repo = Path(args[0]).expanduser()
    hits = sorted(repo.rglob("rocknixds_artwork_manager/device.py"))
    hits = [h for h in hits if ".git" not in h.parts and "__pycache__" not in h.parts]
    if not hits:
        sys.exit("device.py nicht gefunden unter %s" % repo)
    if len(hits) > 1:
        print("Mehrere device.py gefunden, nehme die erste:", *hits, sep="\n  ")
    f = hits[0]
    text = f.read_text(encoding="utf-8")
    if "DUALSTATION_MARKERS" in text:
        print("Schon angepasst:", f)
        return 0
    problems = [name for name, s in (("Konstante", OLD_CONST), ("Shell-Prüfung", OLD_TEST)) if s not in text]
    if problems:
        sys.exit("Nicht angepasst – erwartete Stelle nicht gefunden (%s) in %s.\n"
                 "Die Datei hat sich geändert; bitte die Ausgabe an Claude schicken:\n  grep -n DUALSTATION %s"
                 % (", ".join(problems), f, f))
    new = text.replace(OLD_CONST, NEW_CONST, 1).replace(OLD_TEST, NEW_TEST, 1)
    sys.stdout.writelines(difflib.unified_diff(text.splitlines(True), new.splitlines(True),
                                               str(f.relative_to(repo)), str(f.relative_to(repo)) + " (neu)"))
    if check:
        print("\n--check: nichts geändert")
        return 0
    backup = f.with_suffix(".py.vor-rds-patch")
    backup.write_text(text, encoding="utf-8")
    f.write_text(new, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except py_compile.PyCompileError as exc:
        f.write_text(text, encoding="utf-8")
        backup.unlink()
        sys.exit("Syntaxfehler – Änderung zurückgenommen:\n%s" % exc)
    # Shell-Befehl testweise erzeugen und mit sh prüfen (gleiche Erzeugung wie im Paket)
    import shlex
    marker, markers = "/storage/rds-install/es-switch-helper.sh", ("/storage/rds-install/es-switch-helper.sh",
                                                                   "/storage/rgds-test/es-switch-helper.sh")
    cmd = eval('f"' + NEW_TEST.replace('"', '\\"') + '"',
               {"shlex": shlex, "DUALSTATION_MARKER": marker, "DUALSTATION_MARKERS": markers})
    r = subprocess.run(["sh", "-n", "-c", cmd], capture_output=True, text=True)
    if r.returncode:
        f.write_text(text, encoding="utf-8")
        backup.unlink()
        sys.exit("Shell-Befehl fehlerhaft – Änderung zurückgenommen:\n%s\n%s" % (cmd, r.stderr))
    backup.unlink()
    print("\nAngepasst:", f)
    print("Shell-Prüfung auf dem Gerät:", cmd)
    if commit:
        subprocess.run(["git", "-C", str(repo), "add", str(f)], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m",
                        "DualStation/RDS erkennen: Programmordner rds-install (seit RDS v15.2) und rgds-test"], check=True)
        print("Committet – mit „git push“ hochladen.")
    else:
        print("Nicht committet (--commit zum Committen).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
