from __future__ import annotations

import enum


def ensure_enum(enum_type: enum.EnumType, name: str | enum.Enum) -> enum.Enum:
    """
    A enum value is expected.
    However, if a string was given, it will be converted into the enum name.
    If the string is not a valid enum name, a exception will show all valid values.
    """
    if isinstance(name, str):
        try:
            return enum_type(name)
        except KeyError as e:
            names = [i.name for i in enum_type]  # type: ignore
            valid_values = sorted(names)
            valid_values_text = " ".join(valid_values)
            raise KeyError(f"'{name}' is invalid: Use one of: {valid_values_text}") from e

    assert isinstance(name, enum_type)
    assert isinstance(name, enum.Enum)
    return name


class SpPosition(enum.StrEnum):
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


class DS18Index(enum.StrEnum):
    """
    This corresponds to sensor numbering on the Dezentral PCB.
    """

    UNUSED_A = enum.auto()
    UNUSED_B = enum.auto()
    UNTEN_A = enum.auto()
    UNTEN_B = enum.auto()
    MITTE_A = enum.auto()
    MITTE_B = enum.auto()
    OBEN_A = enum.auto()
    OBEN_B = enum.auto()

    @property
    def index2(self) -> int:
        return {
            DS18Index.UNUSED_A: 0,
            DS18Index.UNUSED_B: 1,
            DS18Index.UNTEN_A: 2,
            DS18Index.UNTEN_B: 3,
            DS18Index.MITTE_A: 4,
            DS18Index.MITTE_B: 5,
            DS18Index.OBEN_A: 6,
            DS18Index.OBEN_B: 7,
        }[self]

    def __repr__(self) -> str:
        return f"'{self.name}'"


assert DS18Index.UNTEN_A.index2 == SpPosition.UNTEN.ds18_index_a
assert DS18Index.UNTEN_B.index2 == SpPosition.UNTEN.ds18_index_b
assert DS18Index.MITTE_A.index2 == SpPosition.MITTE.ds18_index_a
assert DS18Index.MITTE_B.index2 == SpPosition.MITTE.ds18_index_b
assert DS18Index.OBEN_A.index2 == SpPosition.OBEN.ds18_index_a
assert DS18Index.OBEN_B.index2 == SpPosition.OBEN.ds18_index_b
