# Mode Automatik

## Zwischenstand Januar 2025

Hier ein Beispiel puent, Zeitbereich from=1735711767955&to=1736718791175.

Deutlich weniger Brennerstarts als beim "Manuellen" Betrieb.
Ruhig und stabil.


Brenner

<img src="./images/2025_januar_puent_uebersicht.png" />

- grüne Linie: brenner_1, blaue Linie: brenner_2
- Die Brenner modulieren entweder auf 100% oder 30%
- Geht die Linie auf -3%, so bedeutet das "saugen": Pellets werden in den Tagesbehälter gesogen.
- Die ersten 5 Tage brennt brenner_2 nonstop durch.
- Am 6. Januar muss der brenner_1 zugeschaltet werden. brenner_2 wird kurz darauf gelöscht weil es in der Nacht zu viel Energie hatte (brennen die Brenner auf "30%", so leisten sie je 20kW, also total 40kW, 50% der Nominalleistung)
- Am 12. Januar wird brenner_2 zugeschaltet und brenner_1 wird bald darauf gelöscht

Über 12 Tage musste zwei mal ein Brenner gezündet werden. Das ist super. Der Tagesbehälter wird regelmässig und rechtzeitig gefüllt. Je nach Bedarf der Siedlung wird sporadisch ein zweiter Brenner zugeschaltet. 

<img src="./images/2025_januar_puent_verbrauch.png" />


- Geschätzer Verbrauch eines Hauses (Median aller Häuser).
- Morgens um 8 Uhr Peak von ca. 3.5 kW. In der Nacht rund 250 Watt.
- Aufgrund dieser Messung mache ich eine Prognose und lade die dezentralen Speicher entsprechend. Der Morgentliche Peak könnte ohne Vorladen nicht oder nur durch zuschalten des zweiten Brenners bewältigt werden.

Fernleitung Rücklauftemperatur

<img src="./images/2025_januar_puent_Tfr_C.png" />

- Die Rücklauftemperatur aus der Siedlung ist im Mittel etwa auf 42C. 
- Die Rücklauftemperatur entspricht fast exakt der Vorlauftemperatur der Brenner.
- Dieser Temperatur sollte so tief wie möglich sein. Tiefer als 35C wären gut. 

Probleme welche zu einer hohen Rücklauftemperatur führen:
- Brenner lassen sich nicht genügend Tief modulieren, ich muss in der Nacht die Siedlung dadurch zu viel füllen.
- Ich kann nur entweder auf 100% oder 30% modulieren. Zwischenwerde kriege ich nicht hin.
- Schlechte Eigenschaften der dezentralen Speicher, Durchmischung wegen den Registern, ungünstige Position der Register.
- Die Reserve in der Siedlung muss höher sein weil in der kalten Jahreszeit mehr Lastpeaks auftreten und ich dieses sonst nicht abfangen kann. Das Zünden eines Brenners braucht bis zu 50 Minuten. Entsprechend muss ich Reserve haben.

Fernleitung Vorlauftemperatur

<img src="./images/2025_januar_puent_Tfv_C.png" />

- Die Vorlauftemperatur der Fernleitung Tfv wähle ich entpsrechend der Temperatur der dezentralen Speicher welche gerade geladen werden und anhand der Leistung welche ich von den brennern weg bringen muss.
- Durch diese variable Vorlauftemperatur kann ich die Ferluste in der Fernleitung reduzieren und ich kann eine tiefere Rücklauftemperatur erreichen.

Temperatur oben im zentralen Pufferspeicher

<img src="./images/2025_januar_puent_Tsz4_C.png" />

- Die Temperatur oben im zentralen Pufferspeicher ist bei ca. 75C. Tip top.