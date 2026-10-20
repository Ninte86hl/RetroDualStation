#!/bin/bash
# RetroDualStation Artwork Manager – Start über Ports in EmulationStation
D=/storage/.config/retrodualstation
mkdir -p "$D/artwork"
exec python3 "$D/artwork/rds_artwork.py" >"$D/artwork/manager.log" 2>&1
