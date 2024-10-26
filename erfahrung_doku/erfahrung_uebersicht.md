# Erfahrung mit einer Holzpellet Heizung von Oekofen

## Ausgangslage

Wir haben zwei Sidlungen. Puent mit 15 Häusern und Bochs mit 11 Häusern. Jede Siedlung hat eine separate Heizzentrale. Hier wurde die Pelletsheizung ersetzt. 
Dezentral, in den Häusern, ist in jedem Haus ein Wärmespeicher. Von diesem wird Heizwärme und Brachwasser bezogen.

![Bild](./images/hydraulik.png)

Die Wärmespeicher in den Häsuern haben ein Register(Wärmetauscher mit einem Rohr im Speicher). Das Wasser von der Heizzentrale ist daher nicht das gleiche Wasser wie jenes in der Bodenheizung von einem Haus. Das Brauchwasser (Duschen, Baden, Waschen) befindet sich in einem Chromstahltank im Wärmespeicher.

Der alte Pellets Brenner rauchte oft. Nach vielen Jahren Qualm haben wir uns entschieden den Brenner zu ersetzen.

## Neu

Wir haben, je Heizzentrale, einen alten Pelletbrenner durch zwei neue Oekofen Pellet Brenner ersetzt. Zudem haben wir neu in der Heizzentrale einen Pufferspeicher.

Die Fernleitung und die dezentralen Anlagen bleiben aus Kostengründen bestehen. Es wäre sinnvoll nur Heizenergie zentral zu erzeugen und Brauchwasser dezentral, z.B. mit einer kleinen Wärmepumpe zu erzeugen. Im Sommer hohe Temperturen über die Fernleitung zu transportieren bringt viele Verluste. Aber das steht hier nicht zur Diskussion.

# Erfahrung in den ersten Monaten
Die Installateure haben prima gearbeitet. Das neue System bringt viele Vorteile.
- Der Pellets-Bunker mit zwei Schnecken hat fast kein Totvolumen mehr (Pellets können komplett geleert werden.)
- Die zwei Brenner PESK41 von Oekofen laufen prima. Was aus dem Kamin kommt sieht nach feuchter Luft aus, weisser Rauch. Keine merklichen Geruchsemissionen.
- Durch den zusätzlichen zentralen Pufferspeicher können die Brennzyklen reduziert werden.
- Die Steuerung funktioniert. Die Temperaturen aller Speicher, zentral und dezentral werden gemessen. Die Brenner, die Fernleitungspumpe und die Ventile dezentral gesteuert. Weniger Brennzylen, allgmein tiefere Temperaturen und damit einhergehend weniger Verluste: super.
- Wir haben eine Notheizung mit Strom. Das gibt Sicherheit.
- Zwei Brenner, zwei saugsysteme, zwei Schnecken im Pellets-Bunker. Redundant. Das gibt Sicherheit.
- Die Brenner sind einfach. Ofentüre auf und man sieht das Feuer. 
- Der Brennteller ist elegant. Pellets werden von unten in der Mitte rauf geschoben, kontinuierlicher Prozess.
- Brennwerttechnik. Die Kamine sind kalt. Vermutlich haben wir einen guten Wirkungsgrad.
- Das saugen der Pellets durch Schläuche. Elegant.


Die Steuerung bietet einen "Manuellen" und einen "Automatischen" Betrieb. Der Manuelle läuft ganz ohne Software. Robust dafür nicht so sparsam.

Hier einige separate Dokumente mit Details:

- [Testbetrieb Manuell](./betrieb_manuell/readme.md) 
- [Speicher bewirtschaftung im Modus Manuell](./speicher_bewirtschaftung/readme.md) 
- [Brenner Startzeit](./brenner_startzeit/readme.md) 
- [Asche und Rauch](./asche_rauch/readme.md) 
- [Modulation der Brenner](./modulation/readme.md) 
- [Interface zu den Brennern](./modbus_relaiskontakte/readme.md) 
- [Pellets zu den Tagesbehältern saugen](./saugen/readme.md) 


Nicht alles ist perfekt aber unter dem Strich ist es eine sehr schöne Lösung. Vielen Dank an dieser Stelle an alle die dazu beigetragen haben.

## Einige Impressionen

Ein Teil der Steuerung: pcb_dezentral (Eigenentwicklung) mit RP2040 und Micropython. Erfassen von Temperaturen, Steuern von Relais und kommunizieren per Modbus.

![Bild](./images/20240605_155812.jpg)

Bestehende Heizregler dezentral.

![Bild](./images/20240614_155023.jpg)
![Bild](./images/20240607_101846.jpg)

Verkabelung der Siedlung, viele Kabel, viele Verbindungen

![Bild](./images/20240907_103643.jpg)

Dezentrale Speicher mit zusätzlichen Sensoren DS18B20

![Bild](./images/20240612_170802.jpg)

Sensoren geklebt am zentralen Pufferspeicher


![Bild](./images/20240825_102801.jpg)
![Bild](./images/20240825_101207.jpg)

Notheizung, Mischventil, Wärmezähler, Fernleitungspumpe im Bau, noch nicht isoliert.

![Bild](./images/20240901_174543.jpg)

Brennteller neu

![Bild](./images/20240901_180650.jpg)
![Bild](./images/20240901_180716.jpg)

Brand

![Bild](./images/20240923_094151138.jpg)
![Bild](./images/20240923_100241590.jpg)

![Bild](./images/20240924_110531425.jpg)
![Bild](./images/20241014_075807.jpg)

Pelletsbunker

![Bild](./images/20240920_142544.jpg)
![Bild](./images/20240920_180817.jpg)
![Bild](./images/20240926_082835350.jpg)
![Bild](./images/pellets.jpg)

Heizzentrale

![Bild](./images/20241025_170356.jpg)

Fernleitungspumpe und Mischventil

![Bild](./images/20241025_173034.jpg)
![Bild](./images/20241025_173037.jpg)

Isolation

![Bild](./images/20240924_220246561.jpg)

![Bild](./images/20241003_203341.jpg)