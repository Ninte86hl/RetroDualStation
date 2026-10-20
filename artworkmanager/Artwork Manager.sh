#!/bin/bash
# RetroDualStation Artwork Manager – Start über Ports in EmulationStation
# Programm und Daten: /storage/roms/ports/artworkmanager
D=/storage/roms/ports/artworkmanager
exec python3 "$D/rds_artwork.py" >"$D/manager.log" 2>&1
