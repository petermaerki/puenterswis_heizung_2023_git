from dataclasses import dataclass
import enum


# class HsmSignal(enum.Enum):
#     UserPressedAcquire = enum.auto()
#     GenicamThreadStarted = enum.auto()
#     UserPressedRelease = enum.auto()
#     GenicamThreadStopped = enum.auto()

#     def __repr__(self) -> str:
#         return f"{self.__class__.__name__}.{self.name}"

@dataclass
class HsmTimeSignal:
    time_s: int
    