from typing import Any, TYPE_CHECKING, Union, List
from pymodbus import ModbusException
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.pdu import ModbusResponse
from zentral.util_scenarios import (
    SCENARIOS,
    ScenarioHausModbusError,
    ScenarioHausModbusException,
    ScenarioHausModbusWrongRegisterCount,
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

        self._dict_modbus_server_id_2_haus = {
            h.config_haus.modbus_server_id: h
            for h in self._context.config_bauabschnitt.haeuser
        }

    def find_by_class_slave(self, cls_scenario, slave: int) -> Any:
        haus = self._dict_modbus_server_id_2_haus.get(slave, None)
        if haus is None:
            return None
        return SCENARIOS.find_by_class_haus(
            cls_scenario=cls_scenario,
            haus=haus,
        )

    async def read_input_registers(
        self,
        address: int,
        count: int = 1,
        slave: int = 0,
        **kwargs: Any,
    ) -> ModbusResponse:
        modbus_error: ScenarioHausModbusException = self.find_by_class_slave(
            cls_scenario=ScenarioHausModbusException,
            slave=slave,
        )
        if modbus_error is not None:
            raise ModbusException("ScenarioHausModbusException")

        modbus_error: ScenarioHausModbusError = self.find_by_class_slave(
            cls_scenario=ScenarioHausModbusError,
            slave=slave,
        )
        if modbus_error is not None:
            rsp = ModbusResponse()
            rsp.function_code = 0xFE
            return rsp

        rsp = await self._modbus_client.read_input_registers(
            address=address,
            count=count,
            slave=slave,
            kwargs=kwargs,
        )

        modbus_error: ScenarioHausModbusWrongRegisterCount = self.find_by_class_slave(
            cls_scenario=ScenarioHausModbusWrongRegisterCount,
            slave=slave,
        )
        if modbus_error is not None:
            rsp.registers = rsp.registers[:-1]

        return rsp

    async def read_holding_registers(
        self,
        address: int,
        count: int = 1,
        slave: int = 0,
        **kwargs: Any,
    ) -> ModbusResponse:
        return await self._modbus_client.read_holding_registers(
            address=address,
            count=count,
            slave=slave,
            kwargs=kwargs,
        )

    async def write_registers(
        self,
        address: int,
        values: List[int],
        slave: int = 0,
        **kwargs: Any,
    ) -> ModbusResponse:
        return await self._modbus_client.write_registers(
            address=address,
            values=values,
            slave=slave,
            kwargs=kwargs,
        )

    async def write_coils(
        self,
        address: int,
        values: list[bool] | bool,
        slave: int = 0,
        **kwargs: Any,
    ) -> ModbusResponse:
        return await self._modbus_client.write_coils(
            address=address,
            values=values,
            slave=slave,
            kwargs=kwargs,
        )
