# Prüfliste v15.2: Installieren, Update, Deinstallieren

Reihenfolge auf dem **RG DS** (`192.168.178.21`), danach **RG DS Plus** (`192.168.178.80`) nur Schritt 1, 6 und 7.
`IP` jeweils ersetzen. Ausgaben der Prüfbefehle an Claude schicken.

## 0. Installer bauen (PC)
Wie bei v15.1 (ES-Binary, canvas-ZIP, Artwork-Manager-Repo, Pillow-Wheel):
```
cd ~/RetroDualStation/retrodualstation && git pull && python3 tools/make-installer.py <ES-Binary> v15.2 <canvas-ZIP> --artwork <AM-Repo> --pillow <Pillow-Wheel>
```
Paket aufs Gerät (danach in ES: Ports → „Install RDS“ bzw. „Update RDS“ starten):
```
IP=192.168.178.21; scp retrodualstation-v15.2.zip root@$IP:/storage/roms/ports/ && ssh root@$IP 'cd /storage/roms/ports && unzip -o -q retrodualstation-v15.2.zip && rm retrodualstation-v15.2.zip && systemctl restart essway'
```

## 1. Update von v15.1 (Umzug rgds-test → rds-install)
Ports → „Install RDS“ starten (bei v15.1 heißt der Eintrag noch so). Danach:
```
IP=192.168.178.21; ssh root@$IP 'ls -ld /storage/rds-install /storage/rgds-test; ls -l /storage/roms/backup; unzip -l /storage/roms/backup/RDS_ORIGINAL_BACKUP.zip; head -c 1500 /storage/rds-install/settings-before-rds.json; echo; grep -E "===|Programmordner|Notfall|gesichert|Hinweis|WARN|Uebergang" /storage/dualstation-install.log | tail -20; ls /storage/.config/system.d/multi-user.target.wants/'
```
Erwartet: nur `rds-install`, ZIP + TXT da, JSON da, Log „Update RDS 15.1 -> v15.2“, Guard verlinkt.
Kurz prüfen: Dual-ES, CC, Gameswitcher, ein Spiel, Power-Menü.

Notfall-ZIP für den Vergleich auf den PC holen:
```
IP=192.168.178.21; mkdir -p ~/rds-test && scp root@$IP:/storage/roms/backup/RDS_ORIGINAL_BACKUP.zip ~/rds-test/
```

## 2. Abbruch der Deinstallation nachstellen
Achtung: spielt die Notfall-Sicherung ein (RDS-Kürzel sind danach weg) – deshalb direkt danach Schritt 3.
```
IP=192.168.178.21; ssh root@$IP 'touch /storage/.config/rds-uninstall.running; sync; reboot'
```
Nach dem Neustart:
```
IP=192.168.178.21; ssh root@$IP 'ls /storage/.config/rds-uninstall.running; tail -3 /storage/dualstation-uninstall.log; systemctl status rds-uninstall-guard --no-pager | head -5'
```
Erwartet: Merker weg, Log „Start: Notfall-Sicherung wiederhergestellt“.

## 3. Deinstallation
Ports → „Uninstall RDS“. Danach Reste suchen:
```
IP=192.168.178.21; ssh root@$IP 'tail -30 /storage/dualstation-uninstall.log; echo ===; ls -ld /storage/rds-install /storage/rgds-test /storage/.config/retrodualstation /storage/.config/rds-uninstall.running /storage/roms/backup/RDS_ORIGINAL_BACKUP.zip 2>&1; ls /storage/.config/system.d /storage/.config/logind.conf.d 2>&1; ls /storage/.config/system.d/*.wants 2>&1; grep -n "RetroDualStation\|RDS_Keys\|Fake_Keyboard\|emulationstation-rgds" /storage/.config/sway/config /storage/.config/mako/config; find /storage/roms/savestates \( -name "*.dss.png" -o -name "*.rdsbak" \) | head; find /storage/.config -name "*.vor-rds-kuerzel" -o -name "*.before-rds"; ls /storage/roms/ports | grep -i -E "rds|artwork"; ls /storage/.config/emulationstation/themes'
```
Erwartet: alles „No such file“, keine Treffer; nur `artworkmanager/` (Daten) darf bleiben.

Vergleich mit dem Stand von vor RDS (Unterschiede an Claude schicken – einige sind bei bestehenden Installationen erwartet):
```
IP=192.168.178.21; cd ~/rds-test && rm -rf orig && mkdir orig && unzip -o -q RDS_ORIGINAL_BACKUP.zip -d orig && for f in $(unzip -Z1 RDS_ORIGINAL_BACKUP.zip); do echo "=== /$f"; ssh root@$IP "cat /$f" | diff "orig/$f" - ; done
```

## 4. Neuinstallation
Paket wie in Schritt 0 kopieren, Ports → „Install RDS“. Danach:
```
IP=192.168.178.21; ssh root@$IP 'grep -E "===|Notfall|gesichert" /storage/dualstation-install.log | tail -10; unzip -l /storage/roms/backup/RDS_ORIGINAL_BACKUP.zip; grep -A1 "Install RDS.sh" /storage/roms/ports/gamelist.xml | head -3'
```
Erwartet: „Neuinstallation“, neue ZIP, Gamelist-Name „Update RDS“. Kurz prüfen wie in Schritt 1.

## 5. Update auf derselben Version (Port-Eintrag „Update RDS“)
Paket erneut kopieren (Schritt 0) – in Ports muss **„Update RDS“** stehen. Starten, danach:
```
IP=192.168.178.21; ssh root@$IP 'grep -E "===|Notfall|Hinweis" /storage/dualstation-install.log | tail -5; ls -l --time-style=+%H:%M /storage/roms/backup/'
```
Erwartet: „Update RDS v15.2 -> v15.2“, ZIP-Zeit unverändert (nicht neu angelegt).

## 6. Single-Modus
Ports → „RDS Single-Screen“: Anbernic/Home/Home 2× tun nichts, keine Vibration, Power kurz wie ROCKNIX.
```
IP=192.168.178.21; ssh root@$IP 'systemctl is-active rds-controlcenter; ls /storage/.config/logind.conf.d/; tail -4 /storage/rds-install/es-switch.log'
```
Erwartet: `inactive`, keine `rds-logind-powerkey.conf`, „Power-Taste: ROCKNIX“. Zurück mit „RDS Dual-Screen“ – alles wieder da.

## 7. Funktionen (beide Geräte)
Laden-Menü (Icon, Automatisch), Home kurz/2×/halten, Schnellwechsel (Schalter, Sperre), Touch nach DraStic,
Bluetooth-Controller, Auto-Laden DraStic (RG DS: Wartezeit 0,3 s).
