from __future__ import annotations

import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Watchdog:
    """
    Contains a list of watchdogs uniquely identified by tag.
    """

    def __init__(self, max_inactivity_s: float) -> None:
        self._max_inactivity_s = max_inactivity_s
        self._last_activity_s: dict[str, float] = {}

    @contextmanager
    def activity(self, tag: str):
        """
        If the code within 'with' succeded, 'last_activity_s' will be updated.
        """
        if tag not in self._last_activity_s:
            # This happens the first time this watchdog has been called for this tag.
            self._last_activity_s[tag] = time.monotonic()

        yield

        self._last_activity_s[tag] = time.monotonic()

    def has_expired(self) -> str | None:
        """
        If any of the watchdogs expired: Raise 'WatchdogExpiredException'
        """
        for tag, last_activity_s in self._last_activity_s.items():
            duration_s = time.monotonic() - last_activity_s
            assert duration_s >= 0.0
            if duration_s > self._max_inactivity_s:
                msg = f"Watchdog modbus-'{tag}' has expired ({duration_s}s > {self._max_inactivity_s}s)!"
                logger.warning(msg=msg)
                return msg

        return None
