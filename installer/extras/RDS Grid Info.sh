#!/bin/bash
# RetroDualStation – Infoleiste in der Rasteransicht (canvas-rds) ein- bzw. ausschalten
# Unter dem Raster auf dem unteren Bildschirm: Spieler, Spielname, Jahr, Bewertung, Genre und die Tastenhilfe.
# Aufruf über Ports in EmulationStation (schaltet um: aus → an → aus). War die Leiste an, schaltet der RDS-Installer
# sie nach einem Update wieder ein (--an); nach einer Neuinstallation des Themes von Hand noch einmal ausführen.
THEME=/storage/.config/emulationstation/themes/canvas-rds
XML="$THEME/_inc/variants/rds-grid-info.xml"
INC='	<include>./_inc/variants/rds-grid-info.xml</include>'
LOG=/storage/rds-grid-info.log
log()    { echo "$(date '+%F %T') $*" >> "$LOG"; }
notify() { curl -s -m 3 -X POST -H 'Content-Type: text/plain' --data "$1" http://127.0.0.1:1234/notify >/dev/null 2>&1; }
msgbox() { curl -s -m 3 -X POST -H 'Content-Type: text/plain' --data "$1" http://127.0.0.1:1234/messagebox >/dev/null 2>&1; }

if [ ! -f "$THEME/theme.xml" ] || [ ! -f "$THEME/_inc/variants/variants.xml" ]; then
    msgbox "Grid info: the canvas-rds theme was not found. Please install RetroDualStation (with the canvas theme) first."
    exit 1
fi

# --an: nur einschalten, ohne Neustart und Meldung (vom RDS-Installer, wenn die Leiste vor dem Update an war)
QUIET=""
[ "$1" = "--an" ] && QUIET=1
if [ -n "$QUIET" ] && grep -q "rds-grid-info.xml" "$THEME/theme.xml"; then
    exit 0
fi

if [ -z "$QUIET" ] && grep -q "rds-grid-info.xml" "$THEME/theme.xml"; then
    # ---- ausschalten
    sed -i '/rds-grid-info\.xml/d' "$THEME/theme.xml"
    rm -f "$XML"
    log "aus"
    notify "Grid info off – EmulationStation restarts..."
    sleep 2
    systemctl restart essway
    exit 0
fi

# ---- einschalten
cp "$THEME/theme.xml" "$THEME/theme.xml.vor-grid-info" 2>/dev/null
cat > "$XML" <<'XMLEOF'
<?xml version="1.0" encoding="UTF-8" ?>
<!--
    RetroDualStation – Grid view with info bar (optional, "RDS Grid Info" in Ports).
    Bottom screen (X 0.5 - 1.0): grid on top, info bar below (players, name, year, rating, genre),
    help buttons at the bottom. Loaded after variants.xml, overrides its grid view.
-->
<theme>
	<formatVersion>7</formatVersion>
	<view name="grid">
		<!-- grid a bit smaller: room for the bar -->
		<imagegrid name="gamegrid">
			<pos>0.5 0.03</pos>
			<size>0.5 0.74</size>
		</imagegrid>

		<!-- bar background (canvas-ds metadata background) -->
		<image name="rds-grid-bar-shadow" extra="true">
			<path>./_inc/images/simple/gamelist-metadata-background-shadow-base.webp</path>
			<origin>0.5 0.5</origin>
			<pos>0.75 0.855</pos>
			<size>0.47 0.15</size>
			<linearSmooth>true</linearSmooth>
			<zIndex>2</zIndex>
			<visible>true</visible>
		</image>
		<image name="rds-grid-bar" extra="true">
			<path>./_inc/images/simple/${gamelistMetadataBackgroundImage}-base.webp</path>
			<origin>0.5 0.5</origin>
			<pos>0.75 0.855</pos>
			<size>0.47 0.11</size>
			<linearSmooth>true</linearSmooth>
			<zIndex>3</zIndex>
			<visible>true</visible>
		</image>

		<!-- Positions follow the pills of the canvas-ds bar graphic (screenshot RG DS 28.10.):
		     row 1: [controller icon | players]  [name ..................]
		     row 2: [calendar icon | year]  [rating]  [genre icon | genre] -->
		<text name="md_players">
			<origin>0 0.5</origin>
			<pos>0.547 0.822</pos>
			<size>0.055 ${metaDatafontSize}</size>
			<fontSize>${metaDatafontSize}</fontSize>
			<fontPath>${fontBold}</fontPath>
			<color>${systemInfoColor}</color>
			<zIndex>4</zIndex>
			<visible>true</visible>
		</text>
		<text name="md_name">
			<origin>0 0.5</origin>
			<pos>0.625 0.822</pos>
			<size>0.35 ${metaDatafontSize}</size>
			<fontSize>${metaDatafontSize}</fontSize>
			<fontPath>${fontBold}</fontPath>
			<color>${systemInfoColor}</color>
			<alignment>left</alignment>
			<zIndex>4</zIndex>
			<visible>true</visible>
		</text>
		<datetime name="md_releasedate">
			<origin>0 0.5</origin>
			<pos>0.547 0.885</pos>
			<size>0.055 ${metaDatafontSize}</size>
			<fontSize>${metaDatafontSize}</fontSize>
			<fontPath>${fontBold}</fontPath>
			<color>${systemInfoColor}</color>
			<format>%Y</format>
			<zIndex>4</zIndex>
			<visible>true</visible>
		</datetime>
		<rating name="md_rating">
			<origin>0 0.5</origin>
			<pos>0.627 0.885</pos>
			<size>0 0.027</size>
			<zIndex>4</zIndex>
			<visible>true</visible>
		</rating>
		<text name="md_genre">
			<origin>0 0.5</origin>
			<pos>0.77 0.885</pos>
			<size>0.205 ${metaDatafontSize}</size>
			<fontSize>${metaDatafontSize}</fontSize>
			<fontPath>${fontBold}</fontPath>
			<color>${systemInfoColor}</color>
			<zIndex>4</zIndex>
			<visible>true</visible>
		</text>

		<!-- help buttons at the bottom of the bottom screen -->
		<helpsystem name="help">
			<origin>0 0.5</origin>
			<pos>0.51 0.965</pos>
			<size>0.48 ${metaDatafontSize}</size>
			<fontSize>0.018</fontSize>
			<fontPath>${fontBold}</fontPath>
			<textColor>${helpTextColor}</textColor>
			<iconColor>${helpTextColor}</iconColor>
			<iconA>./_inc/images/help-button-east.svg</iconA>
			<iconB>./_inc/images/help-button-south.svg</iconB>
			<iconX>./_inc/images/help-button-north.svg</iconX>
			<iconY>./_inc/images/help-button-west.svg</iconY>
			<visible>true</visible>
		</helpsystem>
	</view>
</theme>
XMLEOF
# nach variants.xml einbinden (überschreibt dessen Rasteransicht)
sed -i "\#_inc/variants/variants.xml#a\\$INC" "$THEME/theme.xml"
if ! grep -q "rds-grid-info.xml" "$THEME/theme.xml"; then
    rm -f "$XML"
    msgbox "Grid info: could not change the theme. Nothing was changed. Log: $LOG"
    log "Einbinden fehlgeschlagen"
    exit 1
fi
log "an"
[ -n "$QUIET" ] && exit 0
notify "Grid info on – EmulationStation restarts..."
sleep 2
systemctl restart essway
for i in $(seq 1 60); do sleep 2; curl -s -m 2 http://127.0.0.1:1234/ >/dev/null 2>&1 && break; done
sleep 2
msgbox "Grid info is on. Choose GAMELIST VIEW STYLE > GRID for a system to see it. Run 'RDS Grid Info' again to turn it off."
exit 0
