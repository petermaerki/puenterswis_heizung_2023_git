# Konzept Brennzyklen minimieren
```
energiemangel = ladung_minimum von einem Haus < 0% and  Tsz4 < 60C
```
## Zünden verhindern
Brenner dürfen nur bei energiemangel anlaufen.
```
if not energiemangel:
    if brenner_1 aus:
        relais_2 True # brenner_1 sperren
    if brenner_2 aus:
        relais_4 True # brenner_2 sperren
else:
    relais_2 False # brenner_1 nicht sperren
    relais_4 False # brenner_2 nicht sperren
```


## Zentralspeicher nicht unterkühlen durch zu viel Energiebezug vom zentralen Speicher

Tsz4 hat normalerweise über 65C. Falls Tsz4 unter 60 geht, so kann der brenner nicht genügend Wärme liefern.
```
falls geladen wird und die Pumpe läuft
    if Tsz4 < 60C: Pumpe aus
    if Tsz4 > 60+2: Pumpe wieder ein
```
Bei energiemangel wird Oekofen den ersten brenner starten falls Tsz4 unter 60 ist oder nach zwei Stunden den zweiten brenner starten.

## Auslöschen verhindern

Wenn der zentrale Speicher bei Tsz2 zu warm ist, so löscht Oekofen einen Brenner, später den zweiten.

Mir ist noch unklar ob ich mit einer Wärmeanforderung über relais_3 das verhindern kann.

```
if Tsz2 > 45 C:
    mehr Energie beziehen durch Laden zusätzliche Häuser
```



# Übergänge

```mermaid
stateDiagram-v2
    state BeideBrennerAus

    state EinBrennerEin
    
    state EinBrennerEin

    %% Transitions
    [*] --> BeideBrennerAus
    BeideBrennerAus --> EinBrennerEin: ein
    EinBrennerEin --> BeideBrennerAus: aus
    EinBrennerEin --> ZweiBrennerEin: ein2
    ZweiBrennerEin --> EinBrennerEin: aus2
```

* Einfluss: 'aus': Sperren via Relay
* Einfluss: 'aus': State 'TPM > 60C'
* Einfluss: 'ein': State 'TPO < 65C'
* Einfluss: 'ein2': State 'TPO < 65C' für mehr als 2h

TPOlZentraler Speicher TPO
```mermaid
stateDiagram-v2
    state "TPO > 65C" as TPOgt65
    state "TPO 60 ... 65C" as TPO_60_65
    state "TPO < 60C" as TPOlt60
    %% Transitions
    TPOgt65 --> TPO_60_65
    TPO_60_65 --> TPOgt65
    TPO_60_65 --> TPOlt60
    TPOlt60 --> TPO_60_65
```

Zentraler Speicher TPM
```mermaid
stateDiagram-v2
    state "TPM > 60C" as TPMgt60
    state "TPM < 60C" as TPMlt60
    %% Transitions
    TPMgt60 --> TPMlt60
    TPMlt60 --> TPMgt60
```
