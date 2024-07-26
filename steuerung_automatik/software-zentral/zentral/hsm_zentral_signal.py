class SignalZentralBase:
    def __repr__(self) -> str:
        return self.__class__.__name__


class SignalDrehschalter(SignalZentralBase):
    """
    Will be sent after every modbus communication to the relais.

    The state of the drehschalter may be retrieved here:
    self.ctx.modbus_communication.drehschalter.is_manuell.
    """


class SignalHardwaretestBegin(SignalZentralBase):
    def __init__(self, relais_7_automatik: bool):
        self.relais_7_automatik = relais_7_automatik


class SignalHardwaretestEnd(SignalZentralBase):
    pass


class TimeSignal(SignalZentralBase):
    pass


class LegionellenLadungSignal(SignalZentralBase):
    pass


class SignalError(SignalZentralBase):
    """
    Important:
    If something fails, we have to reiterate sending 'SignalError'.
    As soon as we stop sending 'SignalError', the application assumes that everything is find and the application will restart.
    """

    def __init__(self, why: str):
        self.why = why
