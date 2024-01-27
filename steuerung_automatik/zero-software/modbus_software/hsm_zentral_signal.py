class SignalZentralBase:
    def __repr__(self) -> str:
        return self.__class__.__name__


class TimeSignal(SignalZentralBase):
    pass


class LegionellenLadungSignal(SignalZentralBase):
    pass
