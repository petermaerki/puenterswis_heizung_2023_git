from typing import Any, TYPE_CHECKING, Union, List
from pymodbus import ModbusException
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.pdu import ModbusResponse
from zentral.constants import ModbusExceptionIsError, ModbusExceptionRegisterCount
from zentral.util_scenarios import (
    SCENARIOS,
    ScenarioBase,
    ScenarioHausModbusError,
    ScenarioHausModbusException,
    ScenarioHausModbusWrongRegisterCount,
    ScenarioHausSpTemperatureIncrease,
)
from micropython.portable_modbus_registers import IREGS_ALL

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

    def _find_by_class_slave(self, cls_scenario, slave: int) -> ScenarioBase | None:
        haus = self._dict_modbus_server_id_2_haus.get(slave, None)
        if haus is None:
            return None
        return SCENARIOS.find_by_class_haus(
            cls_scenario=cls_scenario,
            haus=haus,
        )

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
        if self._find_by_class_slave(
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

        if self._find_by_class_slave(
            cls_scenario=ScenarioHausModbusError,
            slave=slave,
        ):
            rsp.function_code = 0xFE

        if rsp.isError():
            raise ModbusExceptionIsError("isError")

        if self._find_by_class_slave(
            cls_scenario=ScenarioHausModbusWrongRegisterCount,
            slave=slave,
        ):
            rsp.registers = rsp.registers[:-1]

        self._assert_register_count(rsp=rsp, expected_register_count=count)

        scenario: ScenarioHausSpTemperatureIncrease = self._find_by_class_slave(
            cls_scenario=ScenarioHausSpTemperatureIncrease,
            slave=slave,
        )
        if scenario is not None:
            for i in range(IREGS_ALL.ds18_temperature_cK.reg, IREGS_ALL.ds18_temperature_cK.reg + IREGS_ALL.ds18_temperature_cK.count):
                rsp.registers[i] += scenario.delta_C * 100.0

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