from __future__ import annotations

import enum
import logging

from zentral.util_persistence import TimeBase, TimeBaseMock

logger = logging.getLogger(__name__)


class ActionBaseEnum(enum.IntEnum):
    @property
    def wartezeit_min(self) -> int:
        return self.value

    @property
    def wartezeit_s(self) -> float:
        return 60.0 * self.wartezeit_min


class ActionTimer:
    def __init__(self, timebase: TimeBase | None = None) -> None:
        self._timebase: TimeBase
        if timebase is None:
            self._timebase = TimeBase()
        else:
            self._timebase = timebase
        self._start_s = 0.0
        self._action: ActionBaseEnum | None = None

    def _log(self, msg: str) -> None:
        logger.info(f"{self.action_name_full} {msg}")

    @property
    def _now_s(self) -> float:
        return self._timebase.monotonic_s

    @property
    def action_name(self) -> str:
        if self._action is None:
            return "-"
        return self._action.__class__.__name__

    @property
    def action_name_full(self) -> str:
        if self._action is None:
            return "-"
        return f"{self.action_name}-{self._action.name}-{self._remaining_s/60.0:0.1f}({self._action.value})"

    @property
    def action(self) -> ActionBaseEnum | None:
        return self._action

    @action.setter
    def action(self, value: ActionBaseEnum) -> None:
        assert isinstance(value, ActionBaseEnum)
        self._action = value
        self._start_s = self._now_s
        self._log("set()")

    def cancel(self) -> None:
        if self._action is None:
            return
        self._log("cancel()")
        self._start_s = 0.0
        self._action = None

    @property
    def _since_start_min(self) -> float:
        since_start_s = self._now_s - self._start_s
        since_start_min = since_start_s / 60.0
        return since_start_min

    @property
    def _remaining_s(self) -> float:
        if self._action is None:
            return 0.0
        return self._start_s + self._action.wartezeit_s - self._now_s

    @property
    def remaining_s(self) -> float:
        result = self._remaining_s
        self._log(f"remaining_s() -> {result:0.1f}")
        return result

    def influxdb_add_fields(self, fields: dict[str, float]) -> None:
        if self._action is None:
            return
        fields[f"actiontimer_{self._action.__class__.__name__}_{self._action.name}_min"] = self._remaining_s / 60.0

    @property
    def is_over(self) -> bool:
        if self._action is None:
            return True
        result = self._remaining_s < 0.0
        self._log(f"is_over() -> {result}")
        return result

    def is_over_and_cancel(self) -> bool:
        over = self.is_over
        if over:
            self.cancel()
        return over

    def set_is_over(self) -> None:
        """
        To be used for debugging
        """
        if self._action is not None:
            self._start_s = self._now_s - self._action.wartezeit_s


def main():
    logging.basicConfig(level=logging.DEBUG)

    class BrennerAction(ActionBaseEnum):
        EIN = 30
        AUS = 16
        MODULIEREN = 15
        NICHTS = 1

    timebase_mock = TimeBaseMock()
    x = ActionTimer(timebase=timebase_mock)

    timebase_mock.now_s = 0.0
    x.action = BrennerAction.EIN

    timebase_mock.now_s = 10.0
    x.is_over

    timebase_mock.now_s = 16.0
    x.remaining_s

    timebase_mock.now_s = 17.0
    grafana_records = {}
    x.influxdb_add_fields(fields=grafana_records)
    print(grafana_records)

    timebase_mock.now_s = 18.0
    x.cancel()
    x.remaining_s

    timebase_mock.now_s = 60.0
    x.action = BrennerAction.AUS

    timebase_mock.now_s = 90.0
    x.remaining_s


if __name__ == "__main__":
    main()
