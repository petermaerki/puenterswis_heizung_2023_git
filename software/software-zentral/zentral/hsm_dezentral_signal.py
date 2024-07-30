from zentral.util_modbus_gpio import ModbusIregsAll2


class SignalDezentralBase:
    def __repr__(self) -> str:
        return self.__class__.__name__


class SignalModbusSuccess(SignalDezentralBase):
    def __init__(self, modbus_iregs_all: ModbusIregsAll2):
        self.modbus_iregs_all: ModbusIregsAll2 = modbus_iregs_all


class SignalModbusFailed(SignalDezentralBase):
    pass
