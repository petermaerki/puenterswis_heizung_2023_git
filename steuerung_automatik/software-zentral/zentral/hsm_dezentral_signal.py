from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zentral.util_modbus_haus import ModbusIregsAll


class SignalDezentralBase:
    def __repr__(self) -> str:
        return self.__class__.__name__


class SignalModbusSuccess(SignalDezentralBase):
    def __init__(self, modbus_iregs_all: "ModbusIregsAll"):
        self.modbus_iregs_all: "ModbusIregsAll" = modbus_iregs_all


class SignalModbusFailed(SignalDezentralBase):
    pass
