#!/bin/bash
# RetroDualStation Artwork Manager – Start über Ports in EmulationStation
# Programm und Daten: /storage/roms/ports/rds-artworkmanager (bis v15.3: artworkmanager)
D=/storage/roms/ports/rds-artworkmanager
export RDS_ARTWORK_DIR="$D"
exec python3 "$D/rds_artwork.py" >"$D/manager.log" 2>&1
