from typing import List


class SignalDezentralBase:
    def __repr__(self) -> str:
        return self.__class__.__name__


class ModbusSuccess(SignalDezentralBase):
    def __init__(self, values: List[int]):
        self.values = values


class ModbusFailed(SignalDezentralBase):
    pass
