#!/bin/sh
# Layout für advanced_drastic (trngaje) auf dem RG DS Plus (2 × 1024×768 nebeneinander = 2048x768) anlegen.
# advanced_drastic bringt nur Layouts für die unterstützten Geräte mit; ohne diese Datei startet es auf dem Plus nicht
# (pRenderer=(nil), kein Bild). Aufruf auf dem Gerät:  sh rds-plus-layout.sh
# Wichtig: ES „Microphone sensitivity“ für NDS auf off lassen (sonst stürzt der Starter ab), in advanced_drastic
# „Enable Device Microphone = no“ (das RDS-Kontrollcenter hört selbst ab, L3 = Mikrofon).
D=/storage/.config/drastic/resources/bg/2048x768
mkdir -p "$D"
cat > "$D/layout.json" <<'JSON'
{
"name":"rgds-plus (RDS)",
"number":2,
"layout":[
{
    "index":0,
    "name":"basic",
    "bg":"",
    "screen0_x":0,
    "screen0_y":0,
    "screen0_w":1024,
    "screen0_h":768,
    "screen1_x":1024,
    "screen1_y":0,
    "screen1_w":1024,
    "screen1_h":768
},
{
    "index":1,
    "name":"pixel",
    "bg":"",
    "screen0_x":128,
    "screen0_y":96,
    "screen0_w":768,
    "screen0_h":576,
    "screen1_x":1152,
    "screen1_y":96,
    "screen1_w":768,
    "screen1_h":576
}
]
}
JSON
echo "Layout angelegt: $D/layout.json"
