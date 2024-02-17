from enum import StrEnum, auto


class SpPosition(StrEnum):
    UNTEN = "unten"
    MITTE = "mitte"
    OBEN = "oben"

    @property
    def ds18_pair_index(self) -> int:
        return {
            self.UNTEN: 1,
            self.MITTE: 2,
            self.OBEN: 3,
        }[self]

    @property
    def tag(self) -> str:
        return f"sp_{self.value}"


class DS18Index(StrEnum):
    """
    This corresponds to sensor numbering on the Dezentral BCB.
    """

    UNUSED_A = auto()
    UNUSED_B = auto()
    UNTEN_A = auto()
    UNTEN_B = auto()
    MITTE_A = auto()
    MITTE_B = auto()
    OBEN_A = auto()
    OBEN_B = auto()

    @property
    def index(self) -> int:
        return {
            self.UNUSED_A: 0,
            self.UNUSED_B: 1,
            self.UNTEN_A: 2,
            self.UNTEN_B: 3,
            self.MITTE_A: 4,
            self.MITTE_B: 5,
            self.OBEN_A: 6,
            self.OBEN_B: 7,
        }[self]


assert DS18Index.UNTEN_A.index == SpPosition.UNTEN.ds18_pair_index * 2
assert DS18Index.MITTE_A.index == SpPosition.MITTE.ds18_pair_index * 2
assert DS18Index.OBEN_A.index == SpPosition.OBEN.ds18_pair_index * 2
