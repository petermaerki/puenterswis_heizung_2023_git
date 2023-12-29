class EnumModbusRegisters:
    HREG_RELAIS_GPIO = 43
    IREGS_ALL = 60


class Ireg:
    def __init__(self, iregsall, reg: int, count: 1):
        self._iregsall = iregsall
        self.reg = reg
        self.count = count

    def set_value(self, values, value, i=0):
        assert isinstance(value, int)
        assert len(values) == self._iregsall.register_count
        assert i < self.count
        values[self.reg + i] = value

    def get_value(self, values, i=0):
        assert len(values) == self._iregsall.register_count
        assert i < self.count
        return values[self.reg + i]


class IregsAll:
    def __init__(self):
        self._all = []
        self._next_reg = 0
        self.version_hw = self._add(0)
        self.version_sw = self._add(1)
        self.reset_cause = self._add(2)
        self.uptime_s = self._add(3)
        self.errors_modbus = self._add(4)
        self.relais_gpio = self._add(5)
        self.temperature_cK = self._add(6, 8)
        self.errors_ds18 = self._add(14, 8)

    def _add(self, reg: int, count=1) -> Ireg:
        assert reg == self._next_reg
        self._next_reg += count
        ireg = Ireg(iregsall=self, reg=reg, count=count)
        self._all.append(ireg)
        return ireg

    @property
    def register_count(self) -> int:
        return self._next_reg
