class SignalZentralBase:
    def __repr__(self) -> str:
        return self.__class__.__name__


class SignalDrehschalter(SignalZentralBase):
    """
    Will be sent after every modbus communication to the relais.
    """

    def __init__(self, manuell: bool):
        self.manuell = manuell


class SignalHardwaretestBegin(SignalZentralBase):
    def __init__(self, relais_7_automatik: bool):
        self.relais_7_automatik = relais_7_automatik


class SignalHardwaretestEnd(SignalZentralBase):
    pass


class TimeSignal(SignalZentralBase):
    pass


class LegionellenLadungSignal(SignalZentralBase):
    pass
