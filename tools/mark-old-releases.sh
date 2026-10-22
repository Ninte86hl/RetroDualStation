#!/bin/bash
# Setzt in alten Releases oben einen Hinweis auf die aktuelle Version (bilingual).
# Aufruf (am PC, gh angemeldet):  bash tools/mark-old-releases.sh v14
# Bereits markierte Releases werden aktualisiert, nicht doppelt markiert.
set -e
REPO=Ninte86hl/RetroDualStation
NEW="${1:?Bitte aktuelle Version angeben, z. B. v14}"
URL="https://github.com/$REPO/releases/latest"
NOTE="> ⚠️ **Outdated – the current version is [$NEW]($URL).** Please download the latest release.
> ⚠️ **Veraltet – aktuell ist [$NEW]($URL).** Bitte das neueste Release laden.
"
for tag in $(gh release list -R "$REPO" --limit 100 --json tagName --jq '.[].tagName'); do
    [ "$tag" = "$NEW" ] && continue
    body="$(gh release view "$tag" -R "$REPO" --json body --jq .body)"
    body="$(printf '%s\n' "$body" | sed '/^> ⚠️ \*\*\(Outdated\|Veraltet\)/d')"   # alten Hinweis entfernen
    printf '%s\n%s\n' "$NOTE" "$body" > /tmp/rds-release-body.md
    gh release edit "$tag" -R "$REPO" --notes-file /tmp/rds-release-body.md >/dev/null
    echo "markiert: $tag"
done
rm -f /tmp/rds-release-body.md
