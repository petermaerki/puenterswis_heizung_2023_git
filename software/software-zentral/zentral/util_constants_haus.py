from enum import Enum, StrEnum, auto


def ensure_enum(enum_type: Enum, name: str | Enum) -> Enum:
    """
    A enum value is expected.
    However, if a string was given, it will be converted into the enum name.
    If the string is not a valid enum name, a exception will show all valid values.
    """
    if isinstance(name, enum_type):
        return name
    assert isinstance(name, str)
    try:
        return enum_type[name]
    except KeyError as e:
        valid_values = sorted([e.name for e in enum_type])
        valid_values_text = " ".join(valid_values)
        raise KeyError(f"'{name}' is invalid: Use one of: {valid_values_text}") from e


class SpPosition(StrEnum):
    UNUSED = "unused"
    "Klemmenpaar DS_0, DS_1"
    UNTEN = "unten"
    "Klemmenpaar DS_2, DS_3"
    MITTE = "mitte"
    "Klemmenpaar DS_4, DS_5"
    OBEN = "oben"
    "Klemmenpaar DS_6, DS_7"

    @property
    def ds18_pair_index(self) -> int:
        return {
            self.UNUSED: 0,
            self.UNTEN: 1,
            self.MITTE: 2,
            self.OBEN: 3,
        }[self]

    @property
    def ds18_index_a(self) -> int:
        return self.ds18_pair_index * 2

    @property
    def ds18_index_b(self) -> int:
        return self.ds18_index_a + 1

    @property
    def tag(self) -> str:
        return f"sp_{self.value}"

    def __repr__(self) -> str:
        return f"'{self.name}'"


class DS18Index(StrEnum):
    """
    This corresponds to sensor numbering on the Dezentral PCB.
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
    def index2(self) -> int:
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

    def __repr__(self) -> str:
        return f"'{self.name}'"


assert DS18Index.UNTEN_A.index2 == SpPosition.UNTEN.ds18_index_a
assert DS18Index.UNTEN_B.index2 == SpPosition.UNTEN.ds18_index_b
assert DS18Index.MITTE_A.index2 == SpPosition.MITTE.ds18_index_a
assert DS18Index.MITTE_B.index2 == SpPosition.MITTE.ds18_index_b
assert DS18Index.OBEN_A.index2 == SpPosition.OBEN.ds18_index_a
assert DS18Index.OBEN_B.index2 == SpPosition.OBEN.ds18_index_b
