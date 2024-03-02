class SignalZentralBase:
    def __repr__(self) -> str:
        return self.__class__.__name__


class SignalHardwaretestBegin:
    def __init__(self, relais_7_automatik: bool):
        self.relais_7_automatik = relais_7_automatik


class SignalHardwaretestEnd:
    pass


class TimeSignal(SignalZentralBase):
    pass


class LegionellenLadungSignal(SignalZentralBase):
    pass
