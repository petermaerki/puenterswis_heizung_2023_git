"""
Notizen zu den Feldern ERROR_1, ERROR_2, ...

  Beispiel:
    50540
    ^^^^  Code,
          Siehe:
          Pelletronic_Touch_Fachmann_VA4_2b_E1650DE 1.5.pdf
          31.1 Übersicht der Störungsmeldungen

        ^ Index of Boiler/Accu starting at 0
          Siehe:
          Error description*
          20240826a_Modbus_Kaskade_2.05.pdf
"""

import dataclasses


@dataclasses.dataclass
class RegDefI:
    address: int
    name: str


@dataclasses.dataclass
class RegDefC(RegDefI):
    pass


REG_DEFS: list[RegDefI] = []

REG_DEFS.extend(
    [
        RegDefI(1, "VERSION"),
        RegDefC(2, "AMBIENT_TEMP_C"),
        RegDefI(3, "PLANT_MODE"),
        RegDefI(5, "FA_COUNT"),
        RegDefI(6, "PU_COUNT"),
        RegDefI(10, "ERROR_1"),
        RegDefI(11, "ERROR_2"),
        RegDefI(12, "ERROR_3"),
        RegDefI(13, "ERROR_4"),
        RegDefI(14, "ERROR_5"),
        RegDefI(15, "EXTERNAL_CASCADE_CONTR"),
        RegDefC(16, "CASCADE_SET_C"),
        RegDefC(17, "CASCADE_ON_TEMP_C"),
        RegDefC(18, "CASCADE_OFF_TEMP_C"),
    ]
)
for offset, prefix in (
    (0, "FA1_"),
    (17, "FA2_"),
):
    REG_DEFS.extend(
        [
            RegDefI(offset + 20, prefix + "MODE"),
            RegDefC(offset + 21, prefix + "TEMP_C"),
            RegDefC(offset + 22, prefix + "TEMP_SET_C"),
            RegDefI(offset + 23, prefix + "MODULATION_PERCENT"),
            RegDefI(offset + 24, prefix + "STATE"),
            RegDefC(offset + 25, prefix + "REGEL_TEMP_C"),
            RegDefC(offset + 26, prefix + "OFF_TEMP_C"),
            RegDefC(offset + 27, prefix + "UW_TEMP_ON_C"),
            RegDefI(offset + 28, prefix + "UW_POSTRUN_MIN"),
            RegDefC(offset + 29, prefix + "UW_REG_RANGE_C"),
            RegDefI(offset + 30, prefix + "UW_MIN_RPM_PERCENT"),
            RegDefI(offset + 31, prefix + "RUNTIME_H"),
            RegDefI(offset + 32, prefix + "STARTS"),
            RegDefI(offset + 33, prefix + "TYPE_kW"),
            RegDefI(offset + 34, prefix + "POWER_kW"),
            RegDefI(offset + 35, prefix + "ENERGY_HOLD"),
            RegDefI(offset + 36, prefix + "MAINTENANCE"),
        ]
    )

for offset, prefix in (
    (0, "PU1_"),
    # (8, "PU2_"),
):
    REG_DEFS.extend(
        [
            RegDefC(offset + 88, prefix + "TPO_IST_C"),
            RegDefC(offset + 89, prefix + "TPM_IST_C"),
            RegDefC(offset + 90, prefix + "MINTEMP_ON_C"),
            RegDefC(offset + 91, prefix + "MINTEMP_OFF_C"),
            RegDefC(offset + 92, prefix + "PUMPTEMP_C"),
            RegDefC(offset + 93, prefix + "HYSTERESIS_C"),
            RegDefI(offset + 94, prefix + "POSTRUN_MIN"),
        ]
    )

DICT_REG_DEFS: dict[str, RegDefI] = {reg.name: reg for reg in REG_DEFS}
