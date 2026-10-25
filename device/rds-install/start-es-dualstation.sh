#!/bin/bash
# Startskript der Dual-Screen-Version von EmulationStation (RG DS Plus, RG DS).
# Wird ueber den essway-Drop-in gestartet (siehe device/system.d/).

# Originale ROCKNIX-Startumgebung laden
. /usr/bin/es_settings

# Wayland-Verbindung wie beim funktionierenden ES-Prozess
export XDG_RUNTIME_DIR=/var/run/0-runtime-dir
export WAYLAND_DISPLAY=wayland-1
export SDL_VIDEODRIVER=wayland
export DISPLAY=:0.0

# Sway-Config anpassen (wird von ROCKNIX bei jedem Boot neu geschrieben)
/storage/rds-install/rgds-sway-fix.sh

# Fenstergroesse = Rechteck um beide Bildschirme (aus screens.cfg; Standard RG DS Plus)
RES="$(awk -F'[=,]' '/^(top|bottom)=/{ if($2+$4>w) w=$2+$4; if($3+$5>h) h=$3+$5 } END{ if(w&&h) print w, h }' \
       /storage/.config/retrodualstation/screens.cfg 2>/dev/null)"
[ -n "$RES" ] || RES="2048 768"

# Der Dateiname muss mit "emulationstation-rgds" beginnen,
# sonst greift die Sway-Regel fuer das globale Vollbild nicht.
exec /storage/rds-install/emulationstation-rgds \
  --log-path /var/log \
  --no-splash \
  --windowed \
  --resolution $RES
