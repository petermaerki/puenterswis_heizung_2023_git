"""
Liest speicher_ladung_prozent

Setzt temperaturen von Brenner 1 und 2
Sperrt Brenner
"""

import logging
import time
import typing

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class HandlerElektroNotheizung:
    ELEKTRO_NOTHEIZUNG_Tsz4_MIN_C = 70.0
    ELEKTRO_NOTHEIZUNG_Tsz4_5MIN_C = 75.0
    ELEKTRO_NOTHEIZUNG_Tsz4_MAX_C = 75.0
    DURATION_MINIMUM_AUS_S = 5 * 60.0

    def __init__(self, now_s: float) -> None:
        self.elektro_notheizung_last_aus_s = now_s

    def update(self, ctx: "Context", betrieb_notheizung: bool) -> None:
        """
        betrieb_notheizung=True: Es ist kein Brenner verfügbar
        """
        if not betrieb_notheizung:
            # Kein Notheizbetrieb: Ausschalten
            ctx.hsm_zentral.relais.relais_1_elektro_notheizung = False
            return

        if ctx.hsm_zentral.relais.relais_1_elektro_notheizung:
            # Notheizung ist ein
            if ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C > self.ELEKTRO_NOTHEIZUNG_Tsz4_MAX_C:
                # Zu warm: Ausschalten
                ctx.hsm_zentral.relais.relais_1_elektro_notheizung = False
                self.elektro_notheizung_last_aus_s = time.monotonic()
            return

        # Notheizung ist aus
        if ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C < self.ELEKTRO_NOTHEIZUNG_Tsz4_MIN_C:
            # Zu kalt: Einschalten
            ctx.hsm_zentral.relais.relais_1_elektro_notheizung = True
            return

        if ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C < self.ELEKTRO_NOTHEIZUNG_Tsz4_5MIN_C:
            duration_aus_s = time.monotonic() - self.elektro_notheizung_last_aus_s
            if duration_aus_s > self.DURATION_MINIMUM_AUS_S:
                # Zu kalt: Einschalten
                ctx.hsm_zentral.relais.relais_1_elektro_notheizung = True
