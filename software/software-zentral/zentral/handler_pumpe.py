import logging
import typing

from zentral.controller_mischventil import PumpeAnlaufzeitMischventil
from zentral.util_action import ActionBaseEnum, ActionTimer

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class PumpeAction(ActionBaseEnum):
    PWM_EIN = 20
    PWM_AUS = 40


class PumpeAusZuKaltAction(ActionBaseEnum):
    AUS = 12.0


class HandlerPumpe:
    _TEMPERATURE_FORCE_PUMPE_AUS_C = 62.0

    def __init__(self, ctx: "Context", now_s: float) -> None:
        self._ctx = ctx
        self.pumpe_anlaufzeit_mischventil = PumpeAnlaufzeitMischventil()
        self._actiontimer_pwm = ActionTimer()
        self._actiontimer_pumpe_aus_zu_kalt = ActionTimer()

    def _pumpe(self, now_s: float, ein: bool) -> None:
        # Relais setzen
        self._ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt = not ein
        self.pumpe_anlaufzeit_mischventil.pumpe(now_s=now_s, ein=ein)

    @property
    def pumpe_is_on(self) -> bool:
        return not self._ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt

    def run_forced(self):
        self._ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt = False

    def tick(self, now_s: float) -> None:
        pumpe_ein = self._get_pumpe_ein(now_s=now_s)
        self._pumpe(now_s=now_s, ein=pumpe_ein)

    def tick_pwm(self, now_s: float) -> None:
        pumpe_ein = self._get_pumpe_ein(now_s=now_s)
        if not pumpe_ein:
            # Spezialfall: Alle Häuser-Ventile sind zu: Unbedingt Pumpe abschalten.
            self._pumpe(now_s=now_s, ein=False)
            self._actiontimer_pwm.cancel()
            return

        if self._ctx.hsm_zentral.is_haeuser_ladung_emergency:
            self._pumpe(now_s=now_s, ein=True)
            self._actiontimer_pwm.cancel()
            return

        if self._actiontimer_pwm is None:
            self._pumpe(now_s=now_s, ein=True)
            self._actiontimer_pwm.action = PumpeAction.PWM_EIN
            return

        if self._actiontimer_pwm.is_over:
            if self._actiontimer_pwm.action == PumpeAction.PWM_EIN:
                # Die EIN-PWM Periode ist vorbei: Pumpe ausschalten
                self._pumpe(now_s=now_s, ein=False)
                self._actiontimer_pwm.action = PumpeAction.PWM_AUS
            else:
                # Die AUS-PWM Periode ist vorbei: Pumpe einschalten
                self._pumpe(now_s=now_s, ein=True)
                self._actiontimer_pwm.action = PumpeAction.PWM_EIN

    def _pumpe_ein_falls_speicher_genug_warm(self, now_s: float) -> bool:
        """
        Die Häuser möchten, dass die Pumpe eingeschaltet wird.
        Wir schalten die Pumpe aber nur ein, wenn der Speicher genug warm ist.
        """
        ctx = self._ctx

        def debug(msg: str) -> None:
            logger.debug(f"{msg}: relais_6_pumpe_gesperrt={ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt} Tsz4_C={ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C:0.1f}")

        if self.pumpe_is_on:
            # Pumpe läuft bereits
            if ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C < self._TEMPERATURE_FORCE_PUMPE_AUS_C:
                debug("Speicher ist zu kalt: Darum Pumpe ausschalten")
                self._actiontimer_pumpe_aus_zu_kalt.action = PumpeAusZuKaltAction.AUS
                return False

            # Speicher genug warm: Pumpe laufen lassen
            return True

        if self._actiontimer_pumpe_aus_zu_kalt.is_over_and_cancel():
            # Pumpe läuft nicht: Einschalten
            return True

        debug(f"Speicher ist noch zu kalt, wir müssen noch {self._actiontimer_pumpe_aus_zu_kalt.remaining_s:0.1f}s warten mit dem Einschalten der Pumpe")
        return False

    def _get_pumpe_ein(self, now_s: float) -> bool:
        """
        Falls mindestens ein Haus das Ventil offen hat, muss die Zentrale die Pumpe starten.
        return True: mindestens ein Haus hat ein Ventil offen
        return False: Ventile aller Häuser sind zu
        spezial: haus_maerki
        """
        if self._ctx.haus_maerki_zu_heiss:
            return True

        for haus in self._ctx.config_etappe.haeuser:
            assert haus.status_haus is not None
            hsm_dezentral = haus.status_haus.hsm_dezentral
            if hsm_dezentral.dezentral_gpio.relais_valve_open:
                # Dieses Haus benötigt Wärme: Pumpe ein!
                return self._pumpe_ein_falls_speicher_genug_warm(now_s=now_s)

        return False
