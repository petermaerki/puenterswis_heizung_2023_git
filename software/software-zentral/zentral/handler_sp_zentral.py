import logging
import typing

if typing.TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class HandlerSpZentral:
    AUF_AB_PROZENT_HYSTERESE = 1.0

    def __init__(self) -> None:
        self.last_ladung_prozent: float | None = None
        self.steigt = True

    def set(self, ladung_prozent: float) -> None:
        if self.last_ladung_prozent is None:
            self.last_ladung_prozent = ladung_prozent

        if ladung_prozent > self.last_ladung_prozent + self.AUF_AB_PROZENT_HYSTERESE:
            self.last_ladung_prozent += self.AUF_AB_PROZENT_HYSTERESE
            self.steigt = True
            logger.debug(f"ladung_aufwaerts = True, last_ladung_prozent_auf_ab {self.last_ladung_prozent}")

        if ladung_prozent < self.last_ladung_prozent - self.AUF_AB_PROZENT_HYSTERESE:
            self.last_ladung_prozent -= self.AUF_AB_PROZENT_HYSTERESE
            self.steigt = False
            logger.debug(f"ladung_aufwaerts = False, last_ladung_prozent {self.last_ladung_prozent}")

    @property
    def sinkt(self) -> bool:
        return not self.steigt
