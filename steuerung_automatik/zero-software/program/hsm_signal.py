import enum
from dataclasses import dataclass

# class HsmSignal(enum.Enum):
#     UserPressedAcquire = enum.auto()
#     GenicamThreadStarted = enum.auto()
#     UserPressedRelease = enum.auto()
#     GenicamThreadStopped = enum.auto()

#     def __repr__(self) -> str:
#         return f"{self.__class__.__name__}.{self.name}"


class HsmSignalType(enum.Enum):
    Time = enum.auto()
    LegionellenLadung = enum.auto()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


@dataclass
class HsmTimeSignal:
    time_s: float
    hsm_signal_type: HsmSignalType = HsmSignalType.Time


class Signal:
    pass


class TimeSignal(Signal):
    def __init__(self, time_s):
        self.time_s = time_s


class LegionellenLadungSignal(Signal):
    pass
