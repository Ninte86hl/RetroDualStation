#!/usr/bin/env python3
"""Baut die Installations-ZIP fuer canvas-ds (RG DS Plus).

Aufruf (im Repo-Ordner):
    python3 tools/make-canvas-installer.py <version>
Beispiel:
    python3 tools/make-canvas-installer.py v8

Holt canvas-ds von toniremi (git clone), legt das Overlay aus
theme/canvas-ds-rgds-plus-overlay darueber und packt alles als
canvas-ds-rgds-plus-<version>.zip. Inhalt (in den Ordner "ports" entpacken):
    Install canvas-ds theme.sh
    .canvas-ds/   install-canvas.sh, VERSION, canvas-ds-rgds-plus/
Nicht enthalten: .git, scripts/ (wird mit diesem Mod nicht benutzt),
"customization examples".
"""
import os, shutil, subprocess, sys, tempfile, zipfile

URL = "https://github.com/toniremi/canvas-ds.git"
repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) != 2:
    sys.exit(__doc__)
version = sys.argv[1]
overlay = os.path.join(repo, "theme", "canvas-ds-rgds-plus-overlay")
out = os.path.join(repo, f"canvas-ds-rgds-plus-{version}.zip")
SKIP_TOP = {".git", "scripts", "customization examples"}
EXEC, FILE = 0o100755 << 16, 0o100644 << 16

tmp = tempfile.mkdtemp()
src = os.path.join(tmp, "canvas-ds")
subprocess.run(["git", "clone", "--depth", "1", URL, src], check=True)
commit = subprocess.run(["git", "-C", src, "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True, check=True).stdout.strip()

# Overlay anwenden (nur die Layout-Dateien, nicht README/tools)
for root, dirs, files in os.walk(overlay):
    rel = os.path.relpath(root, overlay)
    if rel.split(os.sep)[0] == "tools":
        continue
    for f in files:
        if rel == "." and f == "README.md":
            continue
        dst = os.path.join(src, rel, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(root, f), dst)

notice = f"""canvas-ds – RG DS Plus (ROCKNIX DualStation)

canvas-ds by toniremi (https://github.com/toniremi/canvas-ds, commit {commit}),
based on Canvas by Siddy212, artwork and layouts by fagnerpc, system icons by
Zoidburg13. Adapted to the RG DS Plus (2048 x 768) by Ninte86hl with the
overlay from https://github.com/Ninte86hl/RetroDualStation, shared with
toniremi's permission.

License: Creative Commons BY-NC-SA (https://creativecommons.org/licenses/by-nc-sa/2.0/)
- attribution, non-commercial use only, adaptations under the same terms.
"""

def add(z, path, arc, mode):
    info = zipfile.ZipInfo.from_file(path, arc)
    info.external_attr = mode
    info.compress_type = zipfile.ZIP_DEFLATED
    with open(path, "rb") as f:
        z.writestr(info, f.read())

with zipfile.ZipFile(out, "w") as z:
    add(z, os.path.join(repo, "installer", "canvas", "Install canvas-ds theme.sh"), "Install canvas-ds theme.sh", EXEC)
    add(z, os.path.join(repo, "installer", "canvas", "install-canvas.sh"), ".canvas-ds/install-canvas.sh", EXEC)
    z.writestr(zipfile.ZipInfo(".canvas-ds/VERSION"), f"{version} (canvas-ds {commit})\n")
    base = ".canvas-ds/canvas-ds-rgds-plus/"
    z.writestr(zipfile.ZipInfo(base + "RGDS-PLUS-NOTICE.txt"), notice)
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        if rel == ".":
            dirs[:] = sorted(d for d in dirs if d not in SKIP_TOP)
        else:
            dirs.sort()
        for f in sorted(files):
            p = os.path.join(root, f)
            add(z, p, base + os.path.relpath(p, src).replace(os.sep, "/"), FILE)

shutil.rmtree(tmp)
print(out, os.path.getsize(out) // (1024 * 1024), "MiB, canvas-ds", commit)
