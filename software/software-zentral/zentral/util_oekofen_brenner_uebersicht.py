import logging

from zentral.util_modbus_oekofen import FA_Mode, FA_State, OekofenRegisters

logger = logging.getLogger(__name__)


def brenner_uebersicht_prozent(registers: OekofenRegisters | None) -> tuple[int, int]:
    """
    Combine different states of brenner 1 / 2 into one percent value.
    """

    def calculate2(brenner: int) -> int:
        if registers is None:
            # Keine Modbus Verbindung
            return -100

        modulation: int = registers.modulation_percent(brenner=brenner)
        fa_state = registers.fa_state(brenner=brenner)
        fa_mode = registers.fa_mode(brenner=brenner)

        if fa_state == FA_State.ASH:
            # Aus, Asche
            return -40
        if fa_state in (FA_State.PELLET, FA_State.PELLET_SWITCH):
            # Aus, keine Pellets
            return -50
        if fa_state in (FA_State.STOERUNG, FA_State.EINMESSEN):
            # Aus, Stoerung/Einmessen
            return -60
        if modulation >= 30:
            # Ein, brennt
            # [30%..100%]
            return modulation
        if fa_mode == FA_Mode.OFF:
            # Ausgeschaltet durch Benutzer in Touch Screen
            return -30
        if fa_mode in (FA_Mode.ON, FA_Mode.AUTO):
            if fa_state == FA_State.OFF99:
                # automatisch, brennt nicht
                return -20
            if fa_state > FA_State.SUCTION:
                logger.warning(f"Unexpeced combination: brenner={brenner} fa_mode={fa_mode!r} fa_state={fa_state!r}")
                # Programmierfehler
                return -200
            # ein, Brenner startet
            return -10 + fa_state

        logger.info(f"FA1_TEMP_C={registers.FA1_TEMP_C}")

    def calculate(brenner: int) -> int:
        v = calculate2(brenner=brenner)
        assert isinstance(v, int)
        return v

    return calculate(brenner=1), calculate(brenner=2)
