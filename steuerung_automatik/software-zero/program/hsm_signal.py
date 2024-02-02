class SignalBase:
    def __repr__(self) -> str:
        return self.__class__.__name__


class TimeSignal(SignalBase):
    pass


class LegionellenLadungSignal(SignalBase):
    pass
