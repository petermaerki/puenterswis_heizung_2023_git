import asyncio
import logging
import typing

from pymodbus import ModbusException
from pymodbus.client import AsyncModbusSerialClient

from zentral.constants import ModbusAddressHaeuser, ModbusAddressOeokofen, ModbusExceptionNoResponseReceived, Waveshare_4RS232
from zentral.hsm_zentral_signal import SignalDrehschalter, SignalError
from zentral.util_influx import InfluxRecords
from zentral.util_modbus import get_modbus_client
from zentral.util_modbus_dac import Dac
from zentral.util_modbus_exception import exception_handler_and_exit
from zentral.util_modbus_mischventil import Mischventil, MischventilRegisters
from zentral.util_modbus_oekofen import Oekofen, OekofenRegisters
from zentral.util_modbus_pcb_dezentral_heizzentrale import PcbsDezentralHeizzentrale
from zentral.util_modbus_relais import ModbusRelais
from zentral.util_modbus_wrapper import ModbusWrapper
from zentral.util_scenarios import SCENARIOS, ScenarioMischventilModbusNoResponseReceived, ScenarioMischventilModbusSystemExit, ScenarioSetRelais1bis5, ScenarioZentralDrehschalterManuell
from zentral.util_watchdog import Watchdog

if typing.TYPE_CHECKING:
    from context import Context

logger = logging.getLogger(__name__)

MODBUS_SLEEP_S = 1.0

MODBUS_ZENTRAL_MAX_INACTIVITY_S = 10.0


class Drehschalter:
    """
    Drehschalter off is indicated by the waveshare-relais-module
    not beeing powered:
    There whill be 'no_response'.
    However, we wait for 10 consecutively 'no_response' to distinguish
    between flakyness and power off.
    We propagate a signal to hsm-zentral.
    """

    REQUIRED_NO_RESPONSES = 10

    def __init__(self):
        self._no_response_counter = 0

    def ok(self) -> None:
        self._no_response_counter = 0

    def no_response(self) -> None:
        self._no_response_counter += 1

    @property
    def is_manuell(self) -> bool:
        return self._no_response_counter > self.REQUIRED_NO_RESPONSES


class ModbusCommunication:
    def __init__(self, context: "Context"):
        self.context = context
        self._modbus = ModbusWrapper(context=context, modbus_client=self._get_modbus_client(n=Waveshare_4RS232.MODBUS_HAEUSER, baudrate=9600))
        self._modbus_oekofen = ModbusWrapper(context=context, modbus_client=self._get_modbus_client(n=Waveshare_4RS232.MODBUS_OEKOFEN, baudrate=19200))
        self._watchdog_modbus_zentral = Watchdog(max_inactivity_s=MODBUS_ZENTRAL_MAX_INACTIVITY_S)

        self.m = Mischventil(self._modbus, ModbusAddressHaeuser.BELIMO)
        self.r = ModbusRelais(self._modbus, ModbusAddressHaeuser.RELAIS)
        self.a = Dac(self._modbus, ModbusAddressHaeuser.DAC)
        self.pcbs_dezentral_heizzentrale = PcbsDezentralHeizzentrale(is_bochs=context.config_etappe.is_bochs)
        self.drehschalter = Drehschalter()
        self.o = Oekofen(self._modbus_oekofen, ModbusAddressOeokofen.OEKOFEN)

    def _get_modbus_client(self, n: int, baudrate: int) -> AsyncModbusSerialClient:
        return get_modbus_client(n=n, baudrate=baudrate)

    async def connect(self):
        await self._modbus.connect()
        await self._modbus_oekofen.connect()

    async def close(self):
        await self._modbus.close()
        await self._modbus_oekofen.close()

    async def modbus_haeuser_loop(self) -> None:
        from zentral.util_modbus_haus import ModbusHaus

        temperatur_aussen_C = self.context.modbus_communication.pcbs_dezentral_heizzentrale.TaussenU_C
        for haus in self.context.config_etappe.haeuser:
            modbus_haus = ModbusHaus(modbus=self._modbus, haus=haus)
            success = await modbus_haus.handle_haus(haus, self.context.influx, temperatur_aussen_C)
            if success:
                await modbus_haus.handle_haus_gpio(haus)

            if False:
                r = InfluxRecords(haus=haus)
                r.add_fields(fields=haus.status_haus.get_influx_fields())
                await self.context.influx.write_records(records=r)

            # await modbus_haus.reboot_reset(haus=haus)

    async def read_modbus_pcbs_dezentral_heizzentrale(self):
        # We wait for max 20s. This may happen if a pcb reboots.
        retries = 10
        sleep_s = 2.0

        async def read_pcb(pcb: PcbsDezentralHeizzentrale) -> None:
            for retry in range(retries):
                try:
                    await pcb.read(modbus=self._modbus)
                    return
                except ModbusException as e:
                    logger.warning(f"Retry {retry+1}({retries}): {pcb.modbus_label}: {e}")
                    await asyncio.sleep(sleep_s)

            raise SystemExit(f"Failed to communicate with pcb {pcb.modbus_label}!")

        for pcb in self.pcbs_dezentral_heizzentrale.pcbs:
            await read_pcb(pcb)

    async def _handle_modbus(self):
        if True:
            await self.read_modbus_pcbs_dezentral_heizzentrale()

        if True:
            await self.modbus_haeuser_loop()

        self.context.hsm_zentral.controller_process(ctx=self.context)
        if True:
            try:
                _manuell, output_100 = self.context.hsm_zentral.mischventil_stellwert_100_overwrite

                if False:
                    # Messung delay controller mischventil
                    import time

                    logger.info(f"{time.monotonic():06.1f}s {output_100:0.1f}% Tfv_C={self.pcbs_dezentral_heizzentrale.Tfv_C:0.1f}")

                with self._watchdog_modbus_zentral.activity("dac"):
                    await self.a.set_dac_100(output_100=output_100)
            except ModbusException as e:
                logger.warning(f"Dac: {e}")

        if True:
            try:
                await self.pcbs_dezentral_heizzentrale.update_ventilator(modbus=self._modbus)
            except ModbusException as e:
                logger.warning(f"pcb11-ventilator: {e}")

        if True:
            if SCENARIOS.remove_if_present(ScenarioMischventilModbusSystemExit):
                raise SystemExit(f"ScenarioMischventilModbusSystemExit({self.m._modbus_label})")
            try:
                if SCENARIOS.is_present(ScenarioMischventilModbusNoResponseReceived):
                    raise ModbusExceptionNoResponseReceived(ScenarioMischventilModbusNoResponseReceived.__name__)
                with self._watchdog_modbus_zentral.activity("mischventil"):
                    all_registers = await self.m.all_registers
                self.context.hsm_zentral.modbus_mischventil_registers = MischventilRegisters(registers=all_registers)
                logger.debug(f"mischventil: {all_registers=}")
            except ModbusException as e:
                self.context.hsm_zentral.modbus_mischventil_registers = None

                logger.warning(f"Mischventil: {e}")

        if True:
            try:
                if SCENARIOS.is_present(ScenarioZentralDrehschalterManuell):
                    raise ModbusException(ScenarioZentralDrehschalterManuell.__name__)

                relais = self.context.hsm_zentral.relais

                scenario = SCENARIOS.find(ScenarioSetRelais1bis5)
                if scenario is not None:
                    assert isinstance(scenario, ScenarioSetRelais1bis5)
                    relais.relais_1_elektro_notheizung = scenario.relais_1_elektro_notheizung
                    relais.relais_2_brenner1_sperren = scenario.relais_2_brenner1_sperren
                    relais.relais_3_waermeanforderung_beide = scenario.relais_3_waermeanforderung_beide
                    relais.relais_4_brenner2_sperren = scenario.relais_4_brenner2_sperren
                    relais.relais_5_keine_funktion = scenario.relais_5_keine_funktion

                _overwrite, relais_6_pumpe_gesperrt = relais.relais_6_pumpe_gesperrt_overwrite
                _overwrite, relais_0_mischventil_automatik = relais.relais_0_mischventil_automatik_overwrite
                await self.r.set(
                    list_gpio=(
                        relais_0_mischventil_automatik,
                        relais.relais_1_elektro_notheizung,
                        relais.relais_2_brenner1_sperren,
                        relais.relais_3_waermeanforderung_beide,
                        relais.relais_4_brenner2_sperren,
                        relais.relais_5_keine_funktion,
                        relais_6_pumpe_gesperrt,
                        relais.relais_7_automatik,
                    )
                )

                self.drehschalter.ok()
                self.context.hsm_zentral.dispatch(SignalDrehschalter())
            except ModbusException as e:
                self.drehschalter.no_response()
                self.context.hsm_zentral.dispatch(SignalDrehschalter())
                if not self.drehschalter.is_manuell:
                    logger.warning(f"Relais: {e}")

        if False:  # TODO sobald Oekofen in Betrieb
            try:
                with self._watchdog_modbus_zentral.activity("oekofen"):
                    all_registers = await self.o.all_registers
                self.context.hsm_zentral.modbus_oekofen_registers = OekofenRegisters(registers=all_registers)
                self.context.hsm_zentral.modbus_oekofen_registers.append_to_file()
                logger.debug(f"oekofen: {all_registers=}")
            except ModbusException as e:
                self.context.hsm_zentral.modbus_oekofen_registers = None

                logger.warning(f"Oekofen: {e}")

    async def task_modbus(self) -> None:
        async with exception_handler_and_exit(ctx=self.context, task_name="modbus", exit_code=42):
            while True:
                msg = self._watchdog_modbus_zentral.has_expired()
                if msg is not None:
                    self.context.hsm_zentral.dispatch(SignalError(why=msg))
                await self._handle_modbus()
                await asyncio.sleep(MODBUS_SLEEP_S)
