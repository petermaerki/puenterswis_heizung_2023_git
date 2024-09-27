"""
This class implements:
* DONE: A common interface for hardware-modbus and mock-modbus.
* NOT_IMPLEMENTED: Logging of the modbus calls on bit level
* DONE: Unified error handling
* Unified error recovery
* DONE: Modbus calls in two asyncio tasks must not interleave
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Iterator, List, Union

from micropython.portable_modbus_registers import IREGS_ALL, EnumModbusRegisters
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ConnectionException, ModbusException
from pymodbus.pdu import ModbusResponse

from zentral.constants import ModbusExceptionIsError, ModbusExceptionNoResponseReceived, ModbusExceptionRegisterCount
from zentral.util_gpio import ScopeTrigger
from zentral.util_scenarios import (
    SCENARIOS,
    ScenarioBase,
    ScenarioHausModbusError,
    ScenarioHausModbusException,
    ScenarioHausModbusSystemExit,
    ScenarioHausModbusWrongRegisterCount,
    ScenarioHausSpDs18PercentOk,
    ScenarioHausSpTemperatureDiscrepancy,
    ScenarioHausSpTemperatureIncrease,
)

if TYPE_CHECKING:
    from zentral.context import Context
    from zentral.context_mock import ModbusMockClient


TIMEOUT_AFTER_MODBUS_TRANSFER_S = 0.040
"""
0.005: Dezentral had up to 10% rate of modbus no response.
0.010: Dezentral has 0% rate of modbus no response.
0.020: Our choice March 2024 (but some errors, House 2, 1%, with additional pcb_dezentral 10, 11, 12)
0.040: Our choice July 2024
"""
TIMEOUT_AFTER_MODBUS_NO_RESPONSE_S = 0.020
TIMEOUT_AFTER_MODBUS_ERROR_S = 0.020
logger = logging.getLogger(__name__)


class ModbusWrapper:
    def __init__(
        self,
        context: "Context",
        modbus_client: Union[AsyncModbusSerialClient, "ModbusMockClient"],
    ):
        from zentral.context import Context
        from zentral.context_mock import ModbusMockClient

        assert isinstance(context, Context)
        assert isinstance(modbus_client, (AsyncModbusSerialClient, ModbusMockClient))

        self.context = context
        self._modbus_client = modbus_client

        self._dict_modbus_server_id_2_haus = {h.config_haus.modbus_server_id: h for h in self.context.config_etappe.haeuser}

        self._lock = asyncio.Lock()
        self._scope_trigger = ScopeTrigger()

    async def connect(self):
        await self._modbus_client.connect()

    async def close(self):
        assert self._modbus_client is not None
        self._modbus_client.close()
        self._modbus_client = None

    @asynccontextmanager
    async def serialize_modbus_calls(self, slave_label: str):
        """
        Make sure the modbus call do not interleave.
        Specially the sleep at the end must block the start of the next
        modbus call.
        """
        assert isinstance(slave_label, str)

        async with self._lock:
            try:
                yield
                await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
            except ConnectionException as e:
                logger.error(f"{slave_label}: Call SystemExit: {e!r}")
                raise SystemExit(e)
            except ModbusException as e:
                if "No response received" in e.message:
                    logger.debug(f"{slave_label}: No response: {e!r}")
                    with self._scope_trigger.modbus_no_response:
                        await asyncio.sleep(TIMEOUT_AFTER_MODBUS_NO_RESPONSE_S)
                    raise ModbusExceptionNoResponseReceived(e)

                logger.error(f"{slave_label}: {e!r}")
                with self._scope_trigger.modbus_error:
                    await asyncio.sleep(TIMEOUT_AFTER_MODBUS_ERROR_S)
                raise

    def _iter_by_class_slave(self, cls_scenario, slave: int) -> Iterator[ScenarioBase]:
        haus = self._dict_modbus_server_id_2_haus.get(slave, None)
        if haus is None:
            return

        yield from SCENARIOS.iter_by_class_haus(cls_scenario=cls_scenario, haus=haus)

    def _assert_register_count(self, rsp: ModbusResponse, expected_register_count: int) -> None:
        register_count = len(rsp.registers)
        if register_count != expected_register_count:
            raise ModbusExceptionRegisterCount(f"Expected {expected_register_count} registers but got {register_count}!")

    async def read_input_registers(
        self,
        address: int,
        count: int,
        slave: int,
        slave_label: str,
    ) -> ModbusResponse:
        assert address == EnumModbusRegisters.SETGET16BIT_ALL_SLOW
        assert isinstance(slave_label, str)
        assert isinstance(slave, int)

        for scenario in self._iter_by_class_slave(
            cls_scenario=ScenarioHausModbusException,
            slave=slave,
        ):
            raise ModbusException("ScenarioHausModbusException")

        for scenario in self._iter_by_class_slave(
            cls_scenario=ScenarioHausModbusSystemExit,
            slave=slave,
        ):
            raise SystemExit(f"ScenarioHausModbusSystemExit({slave_label})")

        async with self.serialize_modbus_calls(slave_label=slave_label):
            rsp = await self._modbus_client.read_input_registers(
                address=address,
                count=count,
                slave=slave,
                kwargs={},
            )

        for scenario in self._iter_by_class_slave(
            cls_scenario=ScenarioHausModbusError,
            slave=slave,
        ):
            rsp.function_code = 0xFE

        if rsp.isError():
            raise ModbusExceptionIsError("isError")

        for scenario in self._iter_by_class_slave(cls_scenario=ScenarioHausModbusWrongRegisterCount, slave=slave):
            rsp.registers = rsp.registers[:-1]

        for scenario in self._iter_by_class_slave(cls_scenario=ScenarioHausSpDs18PercentOk, slave=slave):
            assert isinstance(scenario, ScenarioHausSpDs18PercentOk)
            ds18_offset = IREGS_ALL.ds18_ok_percent.reg
            reg_index = ds18_offset + scenario.ds18_index.index
            rsp.registers[reg_index] = scenario.ds18_ok_percent

        for scenario in self._iter_by_class_slave(cls_scenario=ScenarioHausSpTemperatureDiscrepancy, slave=slave):
            assert isinstance(scenario, ScenarioHausSpTemperatureDiscrepancy)
            ds18_offset = IREGS_ALL.ds18_temperature_cK.reg
            reg_index = ds18_offset + scenario.ds18_index.index
            rsp.registers[reg_index] += int(100 * scenario.discrepancy_C)

        for scenario in self._iter_by_class_slave(cls_scenario=ScenarioHausSpTemperatureIncrease, slave=slave):
            assert isinstance(scenario, ScenarioHausSpTemperatureIncrease)
            ds18_offset = IREGS_ALL.ds18_temperature_cK.reg

            def increment(ds18_index):
                reg_index = ds18_offset + ds18_index
                rsp.registers[reg_index] += int(100 * scenario.delta_C)

            increment(scenario.position.ds18_index_a)
            increment(scenario.position.ds18_index_b)

        self._assert_register_count(rsp=rsp, expected_register_count=count)

        return rsp

    async def read_holding_registers(
        self,
        address: int,
        count: int,
        slave: int,
        slave_label: str,
    ) -> ModbusResponse:
        async with self.serialize_modbus_calls(slave_label=slave_label):
            rsp = await self._modbus_client.read_holding_registers(
                address=address,
                count=count,
                slave=slave,
                kwargs={},
            )
        if rsp.isError():
            raise ModbusExceptionIsError("isError")

        self._assert_register_count(rsp=rsp, expected_register_count=count)

        return rsp

    async def write_registers(
        self,
        address: int,
        values: List[int],
        slave: int,
        slave_label: str,
    ) -> ModbusResponse:
        assert isinstance(values, (list, tuple))

        # Limit value from 0 to 2**16
        for i, value in enumerate(values):
            assert isinstance(value, int)
            value_16bit = min(max(0, value), 2**16 - 1)

            if value_16bit != value:
                logger.warning(f"Modbus limit to 16 bits: {value} has been truncated to {value_16bit}!")
                values[i] = value_16bit

        async with self.serialize_modbus_calls(slave_label=slave_label):
            rsp = await self._modbus_client.write_registers(
                address=address,
                values=values,
                slave=slave,
                kwargs={},
            )
        if rsp.isError():
            raise ModbusExceptionIsError("isError")

        self._assert_register_count(rsp=rsp, expected_register_count=0)
        return rsp

    async def write_coils(
        self,
        address: int,
        values: List[bool],
        slave: int,
        slave_label: str,
    ) -> ModbusResponse:
        assert isinstance(values, (list, tuple))

        async with self.serialize_modbus_calls(slave_label=slave_label):
            rsp = await self._modbus_client.write_coils(
                address=address,
                values=values,
                slave=slave,
                kwargs={},
            )
        if rsp.isError():
            raise ModbusExceptionIsError("isError")

        self._assert_register_count(rsp=rsp, expected_register_count=0)
        return rsp
