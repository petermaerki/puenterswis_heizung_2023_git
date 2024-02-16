from typing import Any, TYPE_CHECKING, Iterator, Union, List
from pymodbus import ModbusException
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.pdu import ModbusResponse
from micropython.portable_modbus_registers import EnumModbusRegisters, IREGS_ALL
from zentral.constants import ModbusExceptionIsError, ModbusExceptionRegisterCount
from zentral.util_scenarios import (
    SCENARIOS,
    ScenarioBase,
    ScenarioHausModbusError,
    ScenarioHausModbusException,
    ScenarioHausModbusWrongRegisterCount,
    ScenarioHausSpDs18Broken,
)

if TYPE_CHECKING:
    from zentral.context_mock import ModbusMockClient
    from zentral.context import Context


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

    async def connect(self):
        await self._modbus_client.connect()

    async def close(self):
        await self._modbus_client.close()

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
        count: int = 1,
        slave: int = 0,
        **kwargs: Any,
    ) -> ModbusResponse:
        assert address == EnumModbusRegisters.SETGET16BIT_ALL

        for scenario in self._iter_by_class_slave(
            cls_scenario=ScenarioHausModbusException,
            slave=slave,
        ):
            raise ModbusException("ScenarioHausModbusException")

        rsp = await self._modbus_client.read_input_registers(
            address=address,
            count=count,
            slave=slave,
            kwargs=kwargs,
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
        count: int = 1,
        slave: int = 0,
        **kwargs: Any,
    ) -> ModbusResponse:
        rsp = await self._modbus_client.read_holding_registers(
            address=address,
            count=count,
            slave=slave,
            kwargs=kwargs,
        )
        if rsp.isError():
            raise ModbusExceptionIsError("isError")

        self._assert_register_count(rsp=rsp, expected_register_count=count)

        return rsp

    async def write_registers(
        self,
        address: int,
        values: List[int],
        slave: int = 0,
        **kwargs: Any,
    ) -> ModbusResponse:
        rsp = await self._modbus_client.write_registers(
            address=address,
            values=values,
            slave=slave,
            kwargs=kwargs,
        )
        if rsp.isError():
            raise ModbusExceptionIsError("isError")

        self._assert_register_count(rsp=rsp, expected_register_count=0)
        return rsp

    async def write_coils(
        self,
        address: int,
        values: list[bool] | bool,
        slave: int = 0,
        **kwargs: Any,
    ) -> ModbusResponse:
        rsp = await self._modbus_client.write_coils(
            address=address,
            values=values,
            slave=slave,
            kwargs=kwargs,
        )
        if rsp.isError():
            raise ModbusExceptionIsError("isError")

        self._assert_register_count(rsp=rsp, expected_register_count=0)
        return rsp
