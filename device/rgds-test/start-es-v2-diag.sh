#!/bin/bash
# Startskript der Dual-Screen-Version von EmulationStation (RG DS Plus).
# Wird ueber den essway-Drop-in gestartet (siehe device/system.d/).

# Originale ROCKNIX-Startumgebung laden
. /usr/bin/es_settings

# Wayland-Verbindung wie beim funktionierenden ES-Prozess
export XDG_RUNTIME_DIR=/var/run/0-runtime-dir
export WAYLAND_DISPLAY=wayland-1
export SDL_VIDEODRIVER=wayland
export DISPLAY=:0.0

# Sway-Config anpassen (wird von ROCKNIX bei jedem Boot neu geschrieben)
/storage/rgds-test/rgds-sway-fix.sh

# Der Dateiname muss mit "emulationstation-rgds" beginnen,
# sonst greift die Sway-Regel fuer das globale Vollbild nicht.
exec /storage/rgds-test/emulationstation-rgds-v7 \
  --log-path /var/log \
  --no-splash \
  --windowed \
  --resolution 2048 768
