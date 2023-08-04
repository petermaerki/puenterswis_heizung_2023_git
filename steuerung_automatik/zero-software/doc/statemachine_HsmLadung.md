```mermaid
stateDiagram-v2
    Aus: Aus
    state Aus

    Bedarf: Bedarf
    state Bedarf
    Bedarf --> Bedarf: Dummy

    Zwang: Zwang
    state Zwang
    Zwang --> Zwang: Dummy
    [*] --> Aus

    %% Transitions
```
