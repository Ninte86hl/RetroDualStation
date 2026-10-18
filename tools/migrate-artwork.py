#!/usr/bin/env python3
"""ROCKNIX DualStation – move RocknixDS Artwork Manager images to their own names.

Runs ON THE DEVICE (python3 from ROCKNIX, standard library only).

Older versions of the Artwork Manager used the same file names as the
EmulationStation scraper (ScreenScraper), so a new scrape overwrote them:

    Icon  -> <thumbnail> romname-thumb.png    (same name as scraper thumbnails)
    Grid  -> <boxart>    romname-box.png      (same name as scraper box art)
    Hero  -> <image>     romname-image.png    (same name as scraper images)

New scheme (own file names, the scraper never touches them):

    Icon  -> <cartridge> romname-icon.png
    Grid  -> <boxart>    romname-grid.png
    Hero  -> <image>     romname-hero.png

The file name alone does not tell whether an image came from the scraper or
from the Artwork Manager, so the image format decides:

    -thumb  exactly square            -> Icon
    -box    exactly 2:3 (portrait)    -> Grid
    -image  at least 2.5 : 1 (wide)   -> Hero

Everything else is left alone.

Usage (stop EmulationStation first, it rewrites the gamelists on exit):

    python3 migrate-artwork.py              # dry run: only shows what would change
    systemctl stop essway
    python3 migrate-artwork.py --apply      # makes the changes
    systemctl start essway

Before the first change in a system, gamelist.xml is copied to
gamelist.xml.before-artwork-migration (once; an existing copy is kept).
"""
import os
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET

ROMS = os.environ.get("DUALSTATION_ROMS", "/storage/roms")
BACKUP_SUFFIX = ".before-artwork-migration"


def image_size(path):
    """(width, height) of a PNG or JPEG file, or None."""
    try:
        with open(path, "rb") as f:
            head = f.read(26)
            if head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR":
                return struct.unpack(">II", head[16:24])
            if head[:2] == b"\xff\xd8":
                f.seek(2)
                while True:
                    marker = f.read(2)
                    if len(marker) < 2 or marker[0] != 0xFF:
                        return None
                    if marker[1] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                                     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                        f.read(3)
                        h, w = struct.unpack(">HH", f.read(4))
                        return w, h
                    length = struct.unpack(">H", f.read(2))[0]
                    f.seek(length - 2, 1)
    except OSError:
        pass
    return None


def is_square(w, h):
    return w == h


def is_grid(w, h):
    return h > w and abs(w * 3 - h * 2) <= 2


def is_hero(w, h):
    return h > 0 and w / h >= 2.5


# (old tag, old suffix, new tag, new suffix, format test, label)
RULES = [
    ("thumbnail", "-thumb", "cartridge", "-icon", is_square, "Icon"),
    ("boxart", "-box", "boxart", "-grid", is_grid, "Grid"),
    ("image", "-image", "image", "-hero", is_hero, "Hero"),
]


def resolve(system_dir, text):
    if text.startswith("./"):
        return os.path.join(system_dir, text[2:])
    if os.path.isabs(text):
        return text
    return os.path.join(system_dir, text)


def main():
    apply = "--apply" in sys.argv[1:]

    if apply:
        try:
            active = subprocess.run(["systemctl", "is-active", "essway"],
                                    capture_output=True, text=True).stdout.strip()
        except OSError:
            active = ""
        if active == "active":
            sys.exit("EmulationStation is running. First: systemctl stop essway")

    print("ROCKNIX DualStation – artwork migration", "(APPLY)" if apply else "(dry run, nothing is changed)")
    total = {label: 0 for *_, label in RULES}
    skipped = 0

    for system in sorted(os.listdir(ROMS)):
        system_dir = os.path.join(ROMS, system)
        gamelist = os.path.join(system_dir, "gamelist.xml")
        if not os.path.isfile(gamelist):
            continue
        try:
            tree = ET.parse(gamelist)
        except ET.ParseError as exc:
            print(f"  {system}: gamelist.xml not readable ({exc}), skipped")
            continue

        changes = []  # (game element, old tag, new tag, old path, new path, new text, label)
        for game in tree.getroot().iter("game"):
            for old_tag, old_suf, new_tag, new_suf, test, label in RULES:
                el = game.find(old_tag)
                if el is None or not el.text:
                    continue
                text = el.text.strip()
                stem, ext = os.path.splitext(text)
                if not stem.endswith(old_suf):
                    continue
                path = resolve(system_dir, text)
                size = image_size(path)
                if not size or not test(*size):
                    continue
                if new_tag != old_tag and game.find(new_tag) is not None:
                    print(f"  {system}: {os.path.basename(path)} – <{new_tag}> already set, skipped")
                    skipped += 1
                    continue
                new_text = stem[: -len(old_suf)] + new_suf + ext
                new_path = resolve(system_dir, new_text)
                if os.path.exists(new_path):
                    print(f"  {system}: {os.path.basename(new_path)} already exists, skipped")
                    skipped += 1
                    continue
                changes.append((game, old_tag, new_tag, path, new_path, new_text, label, size))

        if not changes:
            continue

        print(f"\n{system}: {len(changes)} image(s)")
        for game, old_tag, new_tag, path, new_path, new_text, label, size in changes:
            print(f"  {label:4}  {os.path.basename(path)} ({size[0]}x{size[1]})"
                  f"  ->  {os.path.basename(new_path)}  <{new_tag}>")
            total[label] += 1

        if apply:
            backup = gamelist + BACKUP_SUFFIX
            if not os.path.exists(backup):
                shutil.copy2(gamelist, backup)
            for game, old_tag, new_tag, path, new_path, new_text, label, size in changes:
                os.rename(path, new_path)
                old_el = game.find(old_tag)
                if new_tag == old_tag:
                    old_el.text = new_text
                else:
                    game.remove(old_el)
                    ET.SubElement(game, new_tag).text = new_text
            if hasattr(ET, "indent"):
                ET.indent(tree, space="\t")
            tree.write(gamelist, encoding="utf-8", xml_declaration=True)

    print("\nSummary:", ", ".join(f"{k}: {v}" for k, v in total.items()), f"– skipped: {skipped}")
    if not apply:
        print("Nothing was changed. To apply: systemctl stop essway, then run again with --apply.")


if __name__ == "__main__":
    main()
