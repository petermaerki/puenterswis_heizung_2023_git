class EnumModbusRegisters:
    HREG_RELAIS_GPIO = 43
    IREGS_ALL = 60


class Ireg:
    def __init__(self, reg: int, count: 1):
        self.reg = reg
        self.count = count


class IregsAll:
    def __init__(self):
        self._all = []
        self._next_reg = 0
        self.version_hw = self._add(0)
        self.version_sw = self._add(1)
        self.reset_cause = self._add(2)
        self.uptime_s = self._add(3)
        self.errors_modbus = self._add(4)
        self.errors_ds18 = self._add(5)
        self.relais_gpio = self._add(6)
        self.temperature_cK = self._add(7, 8)

        self.values = [2**16-1,]*self.register_count

    def _add(self, reg: int, count=1) -> Ireg:
        assert reg == self._next_reg
        self._next_reg += count
        ireg = Ireg(reg=reg, count=count)
        self._all.append(ireg)
        return ireg

    @property
    def register_count(self) -> int:
        return self._next_reg
