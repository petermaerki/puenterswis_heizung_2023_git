import enum
import logging

from zentral.util_modbus_oekofen import FA_Mode, FA_State, OekofenRegisters, PlantMode

logger = logging.getLogger(__name__)


class EnumBrennerUebersicht(enum.IntEnum):
    BRENNER_STARTET = -10
    AUTOMATISCH_BRENNT_NICHT = -20
    AUSGESCHALTET_DURCH_BENUTZER = -30
    ASCHE_VOLL = -40
    KEINE_PELLETS = -50
    STOERUNG_EINMESSEN = -60
    KEINE_MODUBUS_VERBINDUNG = -100
    PROGRAMMIERFEHLER = -200


def brenner_uebersicht_prozent(registers: OekofenRegisters | None) -> tuple[int, int]:
    """
    Combine different states of brenner 1 / 2 into one percent value.
    """

    def calculate2(brenner_idx1: int) -> int:
        if registers is None:
            # Keine Modbus Verbindung
            return EnumBrennerUebersicht.KEINE_MODUBUS_VERBINDUNG

        plant_mode = registers.plant_mode()
        if plant_mode == PlantMode.OFF:
            # Ausgeschaltet durch Benutzer in Touch Screen
            return EnumBrennerUebersicht.AUSGESCHALTET_DURCH_BENUTZER

        modulation: int = registers.modulation_percent(brenner_idx1=brenner_idx1)
        fa_state = registers.fa_state(brenner_idx1=brenner_idx1)
        fa_mode = registers.fa_mode(brenner_idx1=brenner_idx1)

        if fa_state == FA_State.ASH:
            # Aus, Asche
            return EnumBrennerUebersicht.ASCHE_VOLL
        if fa_state in (FA_State.PELLET, FA_State.PELLET_SWITCH):
            # Aus, keine Pellets
            return EnumBrennerUebersicht.KEINE_PELLETS
        if fa_state in (FA_State.STOERUNG, FA_State.EINMESSEN):
            # Aus, Stoerung/Einmessen
            return EnumBrennerUebersicht.STOERUNG_EINMESSEN
        if modulation >= 30:
            # Ein, brennt
            # [30%..100%]
            return modulation
        if fa_mode == FA_Mode.OFF:
            # Ausgeschaltet durch Benutzer in Touch Screen
            return EnumBrennerUebersicht.AUSGESCHALTET_DURCH_BENUTZER
        if fa_mode in (FA_Mode.ON, FA_Mode.AUTO):
            if fa_state == FA_State.OFF99:
                # automatisch, brennt nicht
                return EnumBrennerUebersicht.AUTOMATISCH_BRENNT_NICHT
            if fa_state > FA_State.SUCTION:
                logger.warning(f"Unexpeced combination: brenner={brenner_idx1} fa_mode={fa_mode!r} fa_state={fa_state!r}")
                # Programmierfehler
                return EnumBrennerUebersicht.PROGRAMMIERFEHLER
            # ein, Brenner startet
            return EnumBrennerUebersicht.BRENNER_STARTET + fa_state

        logger.info(f"FA1_TEMP_C={registers.FA1_TEMP_C}")
        logger.warning(f"Programming error: {modulation=}, {fa_mode}, {fa_state}")
        return EnumBrennerUebersicht.PROGRAMMIERFEHLER

    def calculate(brenner_idx1: int) -> int:
        v = calculate2(brenner_idx1=brenner_idx1)
        assert isinstance(v, int)
        return v

    return calculate(brenner_idx1=1), calculate(brenner_idx1=2)
