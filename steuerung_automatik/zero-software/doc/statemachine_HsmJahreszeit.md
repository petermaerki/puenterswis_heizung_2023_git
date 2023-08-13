```mermaid
stateDiagram-v2
    sommer: sommer
    state sommer

    winter: winter
    state winter
    [*] --> winter

    %% Transitions
    sommer --> winter: gestern wenig energie verbraucht
    winter --> sommer: gestern viel energie verbraucht
```
