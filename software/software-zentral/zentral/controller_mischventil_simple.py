import logging
import time
import typing

from zentral.constants import BETRIEB_ELEKTRO_NOTHEIZUNG
from zentral.controller_base import ControllerMischventilABC

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class ControllerMischventilNone(ControllerMischventilABC):
    ELEKTRO_NOTHEIZUNG_Tsz4_MIN_C = 70.0
    ELEKTRO_NOTHEIZUNG_Tsz4_5MIN_C = 75.0
    ELEKTRO_NOTHEIZUNG_Tsz4_MAX_C = 75.0

    def __init__(self, now_s: float) -> None:
        super().__init__(now_s=now_s)
        self.last_aus_s: float = time.time()

    def _process_elektro_notheizung(self, ctx: "Context") -> None:
        if BETRIEB_ELEKTRO_NOTHEIZUNG:
            if ctx.hsm_zentral.relais.relais_1_elektro_notheizung:
                # Notheizung ist ein
                if ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C > self.ELEKTRO_NOTHEIZUNG_Tsz4_MAX_C:
                    # Zu warm: Ausschalten
                    ctx.hsm_zentral.relais.relais_1_elektro_notheizung = False
                    self.last_aus_s = time.time()
                return

            # Notheizung ist aus
            if ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C < self.ELEKTRO_NOTHEIZUNG_Tsz4_MIN_C:
                # Zu kalt: Einschalten
                ctx.hsm_zentral.relais.relais_1_elektro_notheizung = True
                return

            if ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C < self.ELEKTRO_NOTHEIZUNG_Tsz4_5MIN_C:
                duration_aus_s = time.time() - self.last_aus_s
                if duration_aus_s > 5 * 60.0:
                    # Zu kalt: Einschalten
                    ctx.hsm_zentral.relais.relais_1_elektro_notheizung = True

            return

        # Kein Notheizbetrieb: Ausschalten
        ctx.hsm_zentral.relais.relais_1_elektro_notheizung = False

    def process(self, ctx: "Context", now_s: float) -> None:
        self._process_elektro_notheizung(ctx=ctx)

    def get_credit_100(self) -> float | None:
        """
        Return None: If the controller simple or None does not calculate the credit
        """
        return None


class ControllerMischventilSimple(ControllerMischventilNone):
    """
    Stellgrössen:
    * Pumpe ein/aus
    * Mischventil auf
    """

    def get_credit_100(self) -> float | None:
        """
        Return None: If the controller simple or None does not calculate the credit
        """
        return None

    def pumpe_ein_falls_speicher_genug_warm(self, ctx: "Context"):
        """
        Die Häuser möchten, dass die Pumpe eingeschaltet wird.
        Wir schalten die Pumpe aber nur ein, wenn der Speicher genug warm ist.
        """

        def debug(msg: str) -> None:
            logger.debug(f"{msg}: relais_6_pumpe_gesperrt={ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt} Tsz4_C={ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C:0.1f}")

        if ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt:
            # Pumpe läuft nicht
            if ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C > 65.0:
                # Speicher ist genug warm: Pumpe einschalten
                return True
            debug("Speicher ist noch zu kalt, wir müssen noch warten mit dem Einschalten der Pumpe")
            return False

        # Pumpe läuft bereits
        if ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C < 62.0:
            debug("Speicher ist zu kalt: Darum Pume ausschalten")
            return False
        # Speicher genug warm: Pumpe laufen lassen
        return True

    def get_pumpe_ein(self, ctx: "Context"):
        """
        Falls mindestens ein Haus das Ventil offen hat, muss die Zentrale die Pumpe starten.
        return True: mindestens ein Haus hat ein Ventil offen
        return False: Ventile aller Häuser sind zu
        """
        for haus in ctx.config_etappe.haeuser:
            assert haus.status_haus is not None
            hsm_dezentral = haus.status_haus.hsm_dezentral
            if hsm_dezentral.dezentral_gpio.relais_valve_open:
                # Dieses Haus benötigt Wärme: Pumpe ein!
                return self.pumpe_ein_falls_speicher_genug_warm(ctx=ctx)

        return False

    def process(self, ctx: "Context", now_s: float) -> None:
        self._process_elektro_notheizung(ctx=ctx)
        # This will force a MissingModbusDataException()
        _Tbv2_C = ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tbv2_C

        ctx.hsm_zentral.relais.relais_0_mischventil_automatik = False
        ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt = not self.get_pumpe_ein(ctx=ctx)
        ctx.hsm_zentral.relais.relais_7_automatik = True
