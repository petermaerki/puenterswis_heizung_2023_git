class SignalZentralBase:
    def __repr__(self) -> str:
        return self.__class__.__name__


class SignalDrehschalter(SignalZentralBase):
    """
    Will be sent after every modbus communication to the relais.

    The state of the drehschalter may be retrieved here:
    self.ctx.modbus_communication.drehschalter.is_manuell.
    """

    pass


class SignalHardwaretestBegin(SignalZentralBase):
    def __init__(self, relais_7_automatik: bool):
        self.relais_7_automatik = relais_7_automatik


class SignalHardwaretestEnd(SignalZentralBase):
    pass


class TimeSignal(SignalZentralBase):
    pass


class LegionellenLadungSignal(SignalZentralBase):
    pass
