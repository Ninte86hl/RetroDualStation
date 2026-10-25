#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""RetroDualStation: Originalwerte der Einstellungen sichern, die RDS ändert – und bei der Deinstallation zurücksetzen.

Gesichert wird je Einstellung (nicht die ganze Datei): spätere eigene Änderungen an anderen Einträgen bleiben bei der
Deinstallation erhalten. Jeder Eintrag wird nur beim ersten Mal gemerkt (erstmalige Installation); fehlte er vorher,
wird er beim Zurücksetzen wieder entfernt.

  rds-settings.py save STORE FILE kv|esxml KEY... [--legacy ALTE_SICHERUNG]
  rds-settings.py save-esinput STORE FILE [--legacy ALTE_SICHERUNG]
  rds-settings.py restore STORE
  rds-settings.py snapshot ZIP DATEI[=ALTE_SICHERUNG]...

snapshot: Notfall-Sicherung der ganzen Dateien von vor RDS als ZIP im Format von ROCKNIX' backuptool
(Pfade ohne führenden /, wiederherstellbar mit „unzip -o ZIP -d /“). Wird nur angelegt, wenn es sie noch nicht gibt –
eine spätere Installation überschreibt sie nie. Mit =ALTE_SICHERUNG wird statt der aktuellen Datei die Sicherung
einer früheren RDS-Version eingepackt (dort steht noch der Stand von vor RDS), unter dem Namen der Originaldatei.

kv     = Zeilen „schlüssel = wert“ (RetroArch, DraStic, DSperate)
esxml  = Zeilen <typ name="schlüssel" value="…" /> (es_settings.cfg)
--legacy: Sicherung einer früheren RDS-Version (z. B. *.vor-rds-kuerzel) – dort steht noch der Originalwert.
"""
import json
import os
import re
import sys

ESINPUT_DEV = 'deviceName="retrogame_joypad"'


def rd(path):
    try:
        with open(path, encoding="utf-8", errors="surrogateescape") as f:
            return f.read()
    except OSError:
        return None


def wr(path, text):
    tmp = path + ".rds-tmp"
    with open(tmp, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(text)
    os.replace(tmp, path)


def load(store):
    try:
        data = json.loads(rd(store) or "{}")
    except ValueError:
        data = {}
    data.setdefault("files", {})
    data.setdefault("esinput", {})
    return data


def save_store(store, data):
    wr(store, json.dumps(data, indent=1, ensure_ascii=False) + "\n")


def kv_key(line):
    return line.split("=", 1)[0].strip() if "=" in line and not line.lstrip().startswith("#") else None


def esxml_key(line):
    m = re.match(r'\s*<\w+ name="([^"]+)" value=', line)
    return m.group(1) if m else None


KEYFN = {"kv": kv_key, "esxml": esxml_key}


def find(text, kind, key):
    return next((l for l in text.splitlines() if KEYFN[kind](l) == key), None)


def cmd_save(store, path, kind, keys, legacy):
    use_legacy = bool(legacy and os.path.exists(legacy) and os.path.exists(path))
    src = rd(legacy) if use_legacy else rd(path)
    if src is None:
        return                                      # Datei gibt es nicht – RDS ändert sie dann auch nicht
    data = load(store)
    entry = data["files"].setdefault(path, {"kind": kind, "keys": {}})
    new = [k for k in keys if k not in entry["keys"]]
    for k in new:
        entry["keys"][k] = find(src, kind, k)       # None = gab es vorher nicht
    if new:
        save_store(store, data)
        print("gesichert: %s (%s)%s" % (path, ", ".join(new), " aus " + legacy if use_legacy else ""))


def esinput_block(text):
    """Start/Ende (Zeilenindex) des Blocks des eingebauten Joypads in es_input.cfg."""
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if ESINPUT_DEV in l:
            for j in range(i, len(lines)):
                if "</inputConfig>" in lines[j]:
                    return lines, i, j
    return lines, None, None


def cmd_save_esinput(store, path, legacy):
    data = load(store)
    if path in data["esinput"]:
        return
    src = rd(legacy) if legacy and os.path.exists(legacy) else rd(path)
    if src is None:
        return
    lines, a, b = esinput_block(src)
    if a is None:
        return
    data["esinput"][path] = [l for l in lines[a:b] if "rightanalog" in l]
    save_store(store, data)
    print("gesichert: %s (%d Einträge rechter Stick)" % (path, len(data["esinput"][path])))


def cmd_restore(store):
    data = load(store)
    ok = True
    for path, entry in data["files"].items():
        text = rd(path)
        if text is None:
            continue
        kind, keyfn = entry["kind"], KEYFN[entry["kind"]]
        lines = text.splitlines()
        for key, orig in entry["keys"].items():
            hits = [i for i, l in enumerate(lines) if keyfn(l) == key]
            if orig is None:
                lines = [l for i, l in enumerate(lines) if i not in hits]
            elif hits:
                lines[hits[0]] = orig
                lines = [l for i, l in enumerate(lines) if i not in hits[1:]]
            elif kind == "esxml" and any("</config>" in l for l in lines):
                k = next(i for i, l in enumerate(lines) if "</config>" in l)
                lines.insert(k, orig)
            else:
                lines.append(orig)
        try:
            wr(path, "\n".join(lines) + ("\n" if text.endswith("\n") else ""))
            print("zurückgesetzt: %s (%s)" % (path, ", ".join(entry["keys"])))
        except OSError as exc:
            ok = False
            print("FEHLER: %s: %s" % (path, exc))
    for path, saved in data["esinput"].items():
        text = rd(path)
        if text is None or not saved:
            continue
        lines, a, b = esinput_block(text)
        if a is None or any("rightanalog" in l for l in lines[a:b]):
            continue
        lines[b:b] = saved
        try:
            wr(path, "\n".join(lines) + ("\n" if text.endswith("\n") else ""))
            print("zurückgesetzt: %s (rechter Stick)" % path)
        except OSError as exc:
            ok = False
            print("FEHLER: %s: %s" % (path, exc))
    return ok


def cmd_snapshot(zpath, specs):
    import zipfile
    import time
    if os.path.exists(zpath):
        return True
    os.makedirs(os.path.dirname(zpath), exist_ok=True)
    tmp = zpath + ".rds-tmp"
    done = []
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for spec in specs:
            path, _, legacy = spec.partition("=")
            src = legacy if legacy and os.path.isfile(legacy) else path
            if not os.path.isfile(src):
                continue
            info = zipfile.ZipInfo(os.path.realpath(path).lstrip("/"), time.localtime(os.path.getmtime(src))[:6])
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(src, "rb") as f:
                z.writestr(info, f.read())
            done.append(path + (" (aus %s)" % legacy if src == legacy else ""))
    os.replace(tmp, zpath)
    print("Notfall-Sicherung %s: %s" % (zpath, ", ".join(done) or "keine Dateien"))
    return True


def main(argv):
    legacy = None
    if "--legacy" in argv:
        i = argv.index("--legacy")
        legacy = argv[i + 1] if i + 1 < len(argv) else None
        argv = argv[:i] + argv[i + 2:]
    if len(argv) >= 5 and argv[0] == "save" and argv[3] in KEYFN:
        cmd_save(argv[1], argv[2], argv[3], argv[4:], legacy)
    elif len(argv) == 3 and argv[0] == "save-esinput":
        cmd_save_esinput(argv[1], argv[2], legacy)
    elif len(argv) >= 3 and argv[0] == "snapshot":
        cmd_snapshot(argv[1], argv[2:])
    elif len(argv) == 2 and argv[0] == "restore":
        return 0 if cmd_restore(argv[1]) else 1
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
