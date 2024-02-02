```mermaid
stateDiagram-v2
    aktiv: aktiv
    state aktiv

    ausstehend: ausstehend
    state ausstehend

    ok: ok
    state ok
    [*] --> ok

    %% Transitions
    aktiv --> ok: Legionellen gekillt
    ausstehend --> aktiv: Signal LegionellenLadung
    ok --> ausstehend: Zeit abgelaufen
```
