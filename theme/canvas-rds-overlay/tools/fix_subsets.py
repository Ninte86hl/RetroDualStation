#!/usr/bin/env python3
"""Fix theme options of canvas-ds that the RG DS Plus views depend on.

The options below are removed from the theme configuration and their value
is fixed. Every ifSubset="..." condition on these subsets is evaluated once:
true  -> the clause is removed (element always active),
false -> the element is removed.

    aspect-ratio     = 4-3        (the RG DS Plus screens are 4:3)
    system-view      = carousel   (system view is always the carousel)
    sysgridsize      = automatic  (only used by the system grid)
    autogridsize     = automatic  (game grid: rows follow the theme)
    metadata         = on         (always shown)
    metadata-option  = playtime   (play time instead of rating)

Usage (overlay folder): python3 tools/fix_subsets.py
"""
import glob
from lxml import etree

FIXED = {
    "aspect-ratio": "4-3",
    "system-view": "carousel",
    "sysgridsize": "automatic",
    "autogridsize": "automatic",
    "metadata": "on",
    "metadata-option": "playtime",
}


def evaluate(cond):
    """-> (keep element, remaining condition or None)"""
    rest = []
    for clause in cond.split(","):
        clause = clause.strip()
        if ":" not in clause:
            rest.append(clause)
            continue
        name, values = clause.split(":", 1)
        name = name.strip()
        if name not in FIXED:
            rest.append(clause)
            continue
        if FIXED[name] not in [v.strip() for v in values.split("|")]:
            return False, None
    rest = [c for c in rest if c]
    return True, (",".join(rest) if rest else None)


def fix(path):
    parser = etree.XMLParser(remove_blank_text=False, remove_comments=False)
    tree = etree.parse(path, parser)
    root = tree.getroot()
    changed = 0
    for sub in list(root.iter("subset")):
        if sub.get("name") in FIXED:
            sub.getparent().remove(sub)
            changed += 1
    for el in list(root.iter()):
        if not isinstance(el.tag, str):
            continue
        cond = el.get("ifSubset")
        if cond is None:
            continue
        keep, rest = evaluate(cond)
        if not keep:
            if el.getparent() is not None:
                el.getparent().remove(el)
                changed += 1
            continue
        if rest is None:
            del el.attrib["ifSubset"]
            changed += 1
        elif rest != cond:
            el.set("ifSubset", rest)
            changed += 1
    if changed:
        tree.write(path, encoding="UTF-8", xml_declaration=path.endswith("theme.xml") or None)
    return changed


if __name__ == "__main__":
    for path in sorted(glob.glob("**/*.xml", recursive=True)):
        if path.startswith("tools/"):
            continue
        n = fix(path)
        if n:
            print(f"{path}: {n} change(s)")
