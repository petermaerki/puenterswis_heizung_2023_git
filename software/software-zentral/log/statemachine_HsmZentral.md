```mermaid
stateDiagram-v2
    error: error
    state error
    error --> error: Dummy

    hardwaretest: hardwaretest
    state hardwaretest
    hardwaretest --> hardwaretest: Dummy

    initializing: initializing
    state initializing

    ok: ok
    state ok {
        ok_drehschalterauto: drehschalterauto
        state ok_drehschalterauto {
            ok_drehschalterauto_manuell: manuell
            state ok_drehschalterauto_manuell
            ok_drehschalterauto_manuell --> ok_drehschalterauto_manuell: Dummy

            ok_drehschalterauto_regeln: regeln
            state ok_drehschalterauto_regeln
            [*] --> ok_drehschalterauto_regeln
        }

        ok_drehschaltermanuell: drehschaltermanuell
        state ok_drehschaltermanuell
        [*] --> ok_drehschaltermanuell
    }
    [*] --> initializing

    %% Transitions
```
