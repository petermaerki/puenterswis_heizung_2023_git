def abklingen_1_0(verstrichene_Zeit_s):
    assert verstrichene_Zeit_s >= 0.0
    E = 2.7182
    """Zeitkonstante einer typischen, isolierten Heizleitung"""
    tau_s = 4.0 * 3600.0
    return E ** -(verstrichene_Zeit_s / tau_s)


_KAPAZITAET_WASSER_J_kg_K = 4190


def energie_bonus_leitungssegment_J(wasser_kg, verstrichene_Zeit_s):
    heiss_C = 68.0
    kalt_C = 25.0
    energie_heiss_J = (heiss_C - kalt_C) * wasser_kg * _KAPAZITAET_WASSER_J_kg_K
    energie_J = energie_heiss_J * (
        abklingen_1_0(verstrichene_Zeit_s=verstrichene_Zeit_s) * 2.0 - 1.0
    )
    return energie_J


for verstrichene_Zeit_s in [t * 3600 for t in [0, 1, 2, 3, 4, 10]]:
    print(
        f"Zeit {verstrichene_Zeit_s} s  Energie {energie_bonus_leitungssegment_J(wasser_kg=30.0, verstrichene_Zeit_s=verstrichene_Zeit_s)/1000.0/3600.0:0.1f} kWh"
    )
