class GpioBits:
    """
    RelaisGpio is a 16 bit register word.
    This enum specifies the use of each bit
    """

    RELAIS_VALVE_OPEN = 0
    BUTTON_ZENTRALE = 1
    LED_ZENTRALE_ON = 2
    LED_ZENTRALE_BLINK = 3

    def __init__(self, value):
        assert isinstance(value, int)
        self.value = value

    def _set(self, value: int, bit: int) -> None:
        assert isinstance(bit, int)
        assert value in (0, 1)
        mask = 0x01 << bit
        # Set bit to 0
        self.value &= ~mask
        # Set bit if needed
        if value:
            self.value |= mask

    def _get(self, bit: int) -> bool:
        return 0x01 & (self.value >> bit)

    def changed(self, other: "GpioBits") -> bool:
        """
        We compare the state in Zentral and Dezentral.
        But we ignore the read only bits.
        """
        ignore_mask = 0x01 << self.BUTTON_ZENTRALE  # We ignore BUTTON_ZENTRALE
        v1 = self.value & ~ignore_mask
        v2 = other.value & ~ignore_mask
        return v1 == v2

    @property
    def relais_valve_open(self) -> bool:
        return self._get(bit=self.RELAIS_VALVE_OPEN)

    @relais_valve_open.setter
    def relais_valve_open(self, value: bool) -> None:
        self._set(value=value, bit=self.RELAIS_VALVE_OPEN)

    @property
    def button_zentrale(self) -> bool:
        return self._get(bit=self.BUTTON_ZENTRALE)

    @button_zentrale.setter
    def button_zentrale(self, value: bool) -> None:
        self._set(value=value, bit=self.BUTTON_ZENTRALE)

    @property
    def led_zentrale_on(self) -> bool:
        return self._get(bit=self.LED_ZENTRALE_ON)

    @property
    def led_zentrale_blink(self) -> bool:
        return self._get(bit=self.LED_ZENTRALE_BLINK)

    def set_led_zentrale(self, on, blink) -> None:
        assert on in (0, 1)
        assert blink in (0, 1)
        assert not (on and blink), f"Only 'on' OR 'blink' is allowed: {on=} {blink=}"
        self._set(value=on, bit=self.LED_ZENTRALE_ON)
        self._set(value=blink, bit=self.LED_ZENTRALE_BLINK)


class EnumModbusRegisters:
    SETGET1BIT_REBOOT_RESET = 0x20
    SETGET1BIT_REBOOT_WATCHDOG = 0x21
    SETGET16BIT_GPIO = 0x22
    SETGET16BIT_ALL = 0x40


class Ireg:
    def __init__(self, iregsall: "IregsAll", reg: int, count: 1):
        self._iregsall = iregsall
        self.reg = reg
        self.count = count

    def set_value(self, values: list, value: int, i=0):
        assert isinstance(value, int)
        assert len(values) == self._iregsall.register_count
        assert i < self.count
        values[self.reg + i] = value

    def get_value(self, values: list, i=0):
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
        self.ds18_temperature_cK = self._add(6, 8)
        self.ds18_ok_percent = self._add(14, 8)

    def _add(self, reg: int, count=1) -> Ireg:
        assert reg == self._next_reg
        self._next_reg += count
        ireg = Ireg(iregsall=self, reg=reg, count=count)
        self._all.append(ireg)
        return ireg

    @property
    def register_count(self) -> int:
        return self._next_reg


IREGS_ALL = IregsAll()
