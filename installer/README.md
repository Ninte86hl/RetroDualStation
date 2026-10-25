# Installer (Ports-Menü)

Baut eine ZIP, die man in den Ordner `ports` auf der SD-Karte entpackt und
auf dem Gerät über **Ports → Install ROCKNIX DualStation** startet.
Kein SSH und kein PC-Terminal nötig.

```bash
python3 tools/make-installer.py emulationstation-rgds v9
```

| Datei | Zweck |
|---|---|
| `Install RDS.sh` | Ports-Eintrag, startet `install.sh` über `systemd-run` (außerhalb von ES) |
| `payload/install.sh` | prüft Gerät (DSI-1 + DSI-2 1024×768) und ES-Binary (`ldd`), kopiert alles, entfernt den Installer, schaltet auf Dual |
| `payload/uninstall.sh` | zurück auf Original-ES, entfernt Ports-Einträge, Theme und `/storage/rds-install` |
| `payload/ports/Uninstall RDS.sh` | Ports-Eintrag für die Deinstallation |

Fehler (falsches Gerät, unpassende ROCKNIX-Version) erscheinen als Meldung in
ES; dabei wird nichts verändert. Logs: `/storage/rds-install.log`,
`/storage/rds-uninstall.log`.
