# Mode Manuell für zwei Tage

Puent und Bochs laufen für zwei Tage auf Manuell.
Sensor TPO ist ganz oben im Speicher, TPM ganz unten.

Oekofen Puffer1
- Daueranforderung Puffertemp min Ein 65C
- Daueranforderung Puffertemp min Aus 65C

Brennerstarts
- Puent 3 pro Tag
- Bochs 2.5 pro Tag

Leistung Wärmezähler ca.
- Puent 9 kW
- Bochs 7 kW

## Diskussion
Alles wie erwartet. Obwohl TPM ganz unten montiert ist, wird nie ein dezentraler Speicher zu kalt, immer über 20% Ladung individuell.

Es braucht dann einige Stunden bis der zentrale Speicher an Ladung zunimmt. In dieser Zeit wird aber immer Energie an die dezentralen Speicher geliefert, deren Ladung sinkt in dieser Zeit nicht. Perfekt.

![Bild](./images/puent_zentaler_speicher_leer_uebersicht.png)

![Bild](./images/puent_dezentral.png)

Link auf Grafana

http://maerki.com:3000/d/da82d5b6-3fd8-4534-80e5-da1155c11310/uebersicht?orgId=1&from=1729671625106&to=1729847566926&var-etappe=bochs&var-haus=All&var-reihe=All&var-unten_mitte_oben=All&var-LadungDezentral=individuell&var-verbrauch=sp_verbrauch_avg_W

Screenshots Grafana:
- [Puent](./images/puent_manuell_2_tage_20241025.png)
- [Bochs](./images/bochs_manuell_2_tage_20241025.png)

Die Leistung eines Brenners ist nominal 36 kW (gedrosselt durch Verschliessen von Rohren im Kessel? PESK41 könnte ohne Drosselung 41 kW). Es gibt Zeiten wo der zentrale Speicher längere Zeit leer ist, die Leistung kann dann beim Mischventil abgelesen werden. Hier finde ich Werte von:
- 31 kW
- 33 kW

Passt recht gut.

