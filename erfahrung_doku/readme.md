# Bericht

## Ausgangslage

Wir haben zwei Sidlungen. Jede Siedlung hat eine separate Heizzentrale. Hier wurde 2024 die Pelletsheizung ersetzt. 
Dezentral, in den Häusern, ist in jedem Haus ein Wärmespeicher. Von diesem wird Heizwärme und Brauchwasser bezogen.

||Puent|Bochs| |
|---|---|---|---|
|Häuser pro Etappe|15|11|Häuser|
|Speicher dezentral, je Haus|0.69|0.69|m<sup>3</sup>|
|Speicher dezentral total|10.3|7.6|m<sup>3</sup>|
|Speicher zentral total|1.25|2.5|m<sup>3</sup>|
|Heizleistung vor 2024 nominal|70|55|kW|
|Heizleistung nach 2024 nominal|72|72|kW|
|Fernleitung Fluss, alle Ventile offen|2.3|1.7|m<sup>3</sup>/h|
|Fernleitungspumpe  Druck |0.5|0.5|bar|

Hydraulikschema, vereinfacht

<img src="./images/hydraulik.png" width="400" />


Die Wärmespeicher in den Häsuern haben ein Register (Wärmetauscher mit einem Rohr im Speicher). Das Wasser von der Heizzentrale ist daher nicht das gleiche Wasser wie jenes in der Bodenheizung von einem Haus. Das Brauchwasser (Duschen, Baden, Waschen) befindet sich in einem Chromstahltank (integrierte Warmwasserboiler) im Wärmespeicher.

Der alte Pellets Brenner rauchte oft. Nach vielen Jahren Qualm haben wir uns entschieden, die Brenner zu ersetzen.

## Neu, 2024

Wir haben, je Heizzentrale, den alten Pelletbrenner durch zwei neue Oekofen Pellet Brenner ersetzt. Zudem haben wir neu in der Heizzentrale einen Pufferspeicher.

Die Fernleitung und die dezentralen Anlagen bleiben aus Kostengründen bestehen.

# Erfahrung in den ersten Monaten
Die Installateure haben prima gearbeitet.
Das neue System bringt viele Vorteile.
- Der Pellets-Bunker mit zwei Schnecken hat fast kein Totvolumen mehr (Pellets können komplett geleert werden.)
- Die zwei Brenner PESK41 von Oekofen laufen prima. Was aus dem Kamin kommt sieht nach feuchter Luft aus, weisser Rauch. Keine merklichen Geruchsemissionen.
- Durch den zusätzlichen zentralen Pufferspeicher können die Brennzyklen reduziert werden.
- Die Steuerung funktioniert. Die Temperaturen aller Speicher, zentral und dezentral werden gemessen. Die Brenner, die Fernleitungspumpe und die Ventile dezentral gesteuert. Weniger Brennzylen, allgmein tiefere Temperaturen und damit einhergehend weniger Verluste: super.
- Wir haben eine Notheizung mit Strom. Das gibt Sicherheit.
- Zwei Brenner, zwei saugsysteme, zwei Schnecken im Pellets-Bunker. Redundant. Das gibt Sicherheit.
- Die Brenner sind einfach. Ofentüre auf und man sieht das Feuer. 
- Der Brennteller ist elegant. Pellets werden von unten in der Mitte rauf geschoben, kontinuierlicher Prozess. Sieht sauber aus.
- Brennwerttechnik. Die Kamine sind kalt. Vermutlich haben wir einen guten Wirkungsgrad.
- Das saugen der Pellets durch Schläuche. Brenner frei im Raum aufgestellt. 


Die Steuerung bietet einen "Manuellen" und einen "Automatischen" Betrieb. Der Manuelle läuft ganz ohne Software. Robust dafür nicht so sparsam.

Hier einige separate Dokumente mit Details:

- [Alte Heizung, vor 2024](./betrieb_vor_2024/readme.md) 
- [Testbetrieb Manuell](./betrieb_manuell/readme.md) 
- [Testbetrieb Automatik](./betrieb_automatik/readme.md) 
- [Speicher bewirtschaftung im Modus Manuell](./speicher_bewirtschaftung/readme.md) 
- [Brenner Startzeit](./brenner_startzeit/readme.md) 
- [Asche und Rauch](./asche_rauch/readme.md) 
- [Modulation der Brenner](./modulation/readme.md) 
- [Interface zu den Brennern](./modbus_relaiskontakte/readme.md) 
- [Pellets zu den Tagesbehältern saugen](./saugen/readme.md) 


Nicht alles ist perfekt aber unter dem Strich ist es eine sehr schöne Lösung. Vielen Dank an dieser Stelle an alle die dazu beigetragen haben.

## Einige Impressionen

Ein Teil der Steuerung: pcb_dezentral (Eigenentwicklung) mit RP2040 und Micropython. Erfassen von Temperaturen, Steuern von Relais und kommunizieren per Modbus.

<img src="./images/20240605_155812.jpg" width="400" />

Bestehende Heizregler dezentral.

<img src="./images/20240614_155023.jpg" width="400" />
<img src="./images/20240607_101846.jpg" width="400" />

Verkabelung der Siedlung, viele Kabel, viele Verbindungen

<img src="./images/20240907_103643.jpg" width="400" />

Dezentrale Speicher mit zusätzlichen Sensoren DS18B20

<img src="./images/20240612_170802.jpg" width="400" />

Sensoren geklebt am zentralen Pufferspeicher


<img src="./images/20240825_102801.jpg" width="400" />
<img src="./images/20240825_101207.jpg" width="400" />

Notheizung, Mischventil, Wärmezähler, Fernleitungspumpe im Bau, noch nicht isoliert.

<img src="./images/20240901_174543.jpg" width="400" />

Brennteller neu

<img src="./images/20240901_180650.jpg" width="400" />
<img src="./images/20240901_180716.jpg" width="400" />

Brand

<img src="./images/20240923_094151138.jpg" width="400" />
<img src="./images/20240923_100241590.jpg" width="400" />



Pelletsbunker

<img src="./images/20240920_142544.jpg" width="400" />
<img src="./images/20240920_180817.jpg" width="400" />
<img src="./images/20240926_082835350.jpg" width="400" />
<img src="./images/pellets.jpg" width="400" />



Fernleitungspumpe und Mischventil

<img src="./images/20241025_173034.jpg" width="400" />
<img src="./images/20241025_173037.jpg" width="400" />

Isolation

<img src="./images/20240924_220246561.jpg" width="400" />

Heizzentrale

<img src="./images/20241025_170356.jpg" width="400" />

<img src="./images/20241003_203341.jpg" width="400" />

Kamin, ein Brenner auf 100%

<img src="./images/20240924_110531425.jpg" width="400" />
<img src="./images/20241014_075807.jpg" width="400" />