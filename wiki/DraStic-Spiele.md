🇬🇧 [English](DraStic-Games)

# DraStic: Spiele mit Bildschirmtausch

Manche DS-Spiele tauschen zwischendurch oberen und unteren Bildschirm – z. B. im Laden von *Zelda: Phantom Hourglass*.
Mit **Threaded 3D = An** (ROCKNIX-Standard) bringt DraStic das bei manchen Spielen durcheinander: Das Bild landet auf dem
falschen Bildschirm, der Touch bleibt am alten Platz.

**Lösung je Spiel:** Spiel in ES auswählen → **erweiterte Spieleinstellungen** → **Threaded 3D = Aus**. Dann folgt DraStic
dem Wechsel von selbst, samt Touch. Gilt nur für dieses Spiel, alle anderen behalten Threaded 3D.

**Notlösung:** **L3** bzw. die Kachel **Tauschen** im [Kontrollcenter](Kontrollcenter) tauscht die Bildschirme von Hand.

**Nur RG DS – Follow 3D Renderer:** Der RG DS hat auf **beiden** Bildschirmen Touch. Mit *Follow 3D Renderer = An* folgt
das Touchbild dem 3D-Bild, manchmal nach oben – dann einfach oben tippen. Titelbilder mit 3D auf beiden Bildschirmen
flackern dabei (z. B. Zelda). Der **RG DS Plus** hat nur unten Touch: Dort reagiert mit Follow 3D nichts, wenn das
Touchbild oben liegt – deshalb dort *Follow 3D = Auto/Aus* und *Threaded 3D = Aus* bzw. **L3**.

## Liste

| Spiel | Threaded 3D aus nötig | Stand |
|---|---|---|
| The Legend of Zelda: Phantom Hourglass | ja (Laden, Gegenstände) | getestet mit RDS, RG DS + RG DS Plus |
| The Legend of Zelda: Spirit Tracks | ja (gleiche Technik) | gemeldet, mit RDS noch nicht getestet |
| Metroid (laut Meldung, vermutlich *Prime Hunters*) | ja | gemeldet¹ |
| Dragon Quest IV | ja | gemeldet¹ |
| The Rub Rabbits! | ja | gemeldet¹ |
| Mario Kart DS | nein – läuft mit Threaded 3D richtig | gemeldet¹ |

¹ aus [GammaOSNext Issue #225](https://github.com/TheGammaSqueeze/GammaOSNext/issues/225) (Meldungen u. a. von
[WGB-works](https://github.com/WGB-works)) – dort ebenfalls DraStic auf dem RG DS.

Ruckelt ein Spiel ohne Threaded 3D zu stark, lieber Threaded 3D anlassen und bei Bedarf **L3** nutzen.

**Weitere Spiele gefunden?** Gern als [Issue](https://github.com/Ninte86hl/RetroDualStation/issues) melden – mit
Spielname und ob Threaded 3D aus hilft. Jede Meldung wird in den [Credits](https://github.com/Ninte86hl/RetroDualStation/blob/main/CREDITS.md) genannt.
