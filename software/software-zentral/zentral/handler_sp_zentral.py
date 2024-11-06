import logging
import typing

if typing.TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class HandlerSpZentral:
    AUF_AB_PROZENT_HYSTERESE = 1.0
    AUF_AB_PROZENT_INCREMENT = 1.0

    def __init__(self) -> None:
        self.last_ladung_prozent: float | None = None
        self.steigt = False
        self.sinkt = False
        self._last_change_s: float = 0.0

    def set(self, now_s: float, ladung_prozent: float) -> None:
        if self.last_ladung_prozent is None:
            self.last_ladung_prozent = ladung_prozent

        if ladung_prozent > self.last_ladung_prozent + self.AUF_AB_PROZENT_HYSTERESE:
            self.last_ladung_prozent += self.AUF_AB_PROZENT_INCREMENT
            self.steigt = True
            self.sinkt = False
            self._last_change_s = now_s
            logger.debug(f"ladung_aufwaerts = True, last_ladung_prozent_auf_ab {self.last_ladung_prozent:.1f}")

        if ladung_prozent < self.last_ladung_prozent - self.AUF_AB_PROZENT_HYSTERESE:
            self.last_ladung_prozent -= self.AUF_AB_PROZENT_INCREMENT
            self.steigt = False
            self.sinkt = True
            self._last_change_s = now_s
            logger.debug(f"ladung_aufwaerts = False, last_ladung_prozent {self.last_ladung_prozent}")

        duration_s = now_s - self._last_change_s
        assert duration_s >= 0.0
        if duration_s > 3 * 60.0:
            """Steigt oder Sinkt soll nach einer Zeit wieder aufhoeren"""
            self.steigt = False
            self.sinkt = False


        if duration_s > 30 * 60.0:
            """Steigt oder Sinkt soll periodisch kommen auch wenn die Ladung auf dem gleichen Wert bleibt"""
            if self.last_ladung_prozent > 55.0:
                self.steigt = True
                self.sinkt = False
            else:
                self.steigt = False
                self.sinkt = True
            self._last_change_s = now_s

    @property
    def grafana(self) -> int:
        if self.steigt:
            return 1
        if self.sinkt:
            return -1
        return 0
