from enum import StrEnum


class SpPosition(StrEnum):
    OBEN = "oben"
    MITTE = "mitte"
    UNTEN = "unten"


DS18_PAIR_POSITIONS_HAUS = {
    SpPosition.UNTEN: 1,
    SpPosition.MITTE: 2,
    SpPosition.OBEN: 3,
}
