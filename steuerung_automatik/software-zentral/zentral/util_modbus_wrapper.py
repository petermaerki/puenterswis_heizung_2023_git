"""
This class implements:
* DONE: A common interface for hardware-modbus and mock-modbus.
* NOT_IMPLEMENTED: Logging of the modbus calls on bit level
* DONE: Unified error handling
* Unified error recovery
* DONE: Modbus calls in two asyncio tasks must not interleave
"""

from typing import TYPE_CHECKING, Iterator, Union, List
from contextlib import asynccontextmanager
import asyncio
import logging

from pymodbus.exceptions import ModbusException, ConnectionException
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.pdu import ModbusResponse
from micropython.portable_modbus_registers import EnumModbusRegisters, IREGS_ALL
from zentral.constants import ModbusExceptionIsError, ModbusExceptionRegisterCount
from zentral.util_scenarios import (
    SCENARIOS,
    ScenarioBase,
    ScenarioHausModbusError,
    ScenarioHausModbusException,
    ScenarioHausModbusSystemExit,
    ScenarioHausModbusWrongRegisterCount,
    ScenarioHausSpDs18Broken,
)

if TYPE_CHECKING:
    from zentral.context_mock import ModbusMockClient
    from zentral.context import Context


TIMEOUT_AFTER_MODBUS_TRANSFER_S = 0.1
TIMEOUT_AFTER_MODBUS_ERROR_S = 0.2
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

        self._context = context
        self._modbus_client = modbus_client

        self._dict_modbus_server_id_2_haus = {h.config_haus.modbus_server_id: h for h in self._context.config_etappe.haeuser}

        self._lock = asyncio.Lock()

    async def connect(self):
        await self._modbus_client.connect()

    async def close(self):
        assert self._modbus_client is not None
        self._modbus_client.close()
        self._modbus_client = None

    @asynccontextmanager
    async def serialize_modbus_calls(self, slave_label: int):
        """
        Make sure the modbus call do not interleave.
        Specially the sleep at the end must block the start of the next
        modbus call.
        """
        async with self._lock:
            try:
                yield
                await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
            except ConnectionException as e:
                logger.error(f"{slave_label}: Call SystemExit: {e!r}")
                raise SystemExit(e)
            except ModbusException as e:
                if "No response received" in e.message:
                    logger.error(f"{slave_label}: No response: {e!r}")
                    raise
                logger.error(f"{slave_label}: {e!r}")
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

        for scenario in self._iter_by_class_slave(cls_scenario=ScenarioHausSpDs18Broken, slave=slave):
            assert isinstance(scenario, ScenarioHausSpDs18Broken)
            ds18_offset = IREGS_ALL.ds18_ok_percent.reg
            reg_index = ds18_offset + scenario.ds18_index.index
            rsp.registers[reg_index] = scenario.ds18_ok_percent

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
