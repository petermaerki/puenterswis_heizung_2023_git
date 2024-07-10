"""
* Scenario lifesycle
 * eternal/removable
 * selvedestroyed

* instantiated in flask

* container
  * searchable by
    * class
    * optional: haus

* State: Part of scenario
* Protocol
  * delete
  * print
  * found
"""

import io
import abc
import sys
import time
import inspect
import dataclasses
from typing import Any, Dict, Iterator, List, TYPE_CHECKING, TypeVar, Type
import logging

from zentral.util_constants_haus import DS18Index, SpPosition, ensure_enum

if TYPE_CHECKING:
    from zentral.config_base import Haus


logger = logging.getLogger(__name__)

_FUNC_SCENARIO_ADD = "scenario_add"


class ScenarioBase(abc.ABC):
    def decrement(self) -> None:
        if hasattr(self, "counter"):
            self.counter -= 1
            if self.counter <= 0:
                self.destroy()

        if hasattr(self, "duration_s"):
            now_s = time.monotonic()
            if not hasattr(self, "end_s"):
                self.end_s = now_s + self.duration_s
                return
            remaining_s = self.end_s - now_s
            if remaining_s > 0.0:
                self.duration_s = remaining_s
                return
            self.destroy()

    def destroy(self) -> None:
        SCENARIOS.remove(self)

    @property
    def repl_example(self) -> str:
        return f"{_FUNC_SCENARIO_ADD}({self!r})"

    def assert_valid_hausnummer(self, hausnummern: List[int]) -> None:
        if not hasattr(self, "haus_nummer"):
            return
        if self.haus_nummer not in hausnummern:
            raise ValueError(f"haus_nummer {self.haus_nummer} is not valid. Use one of: {hausnummern}")

    def fix_haus_nummer(self, haus_nummer: int) -> None:
        if not hasattr(self, "haus_nummer"):
            return
        self.haus_nummer = haus_nummer


TScenario = TypeVar("TScenario", bound=ScenarioBase)


class Scenarios:
    def __init__(self):
        self._scenarios: List[ScenarioBase] = []

    def add(self, scenario: ScenarioBase) -> None:
        assert isinstance(scenario, ScenarioBase)

        if isinstance(scenario, ScenarioClearScenarios):
            logger.info("Scenario: Clear")
            self._scenarios.clear()
            return

        logger.info(f"Scenario: Add {scenario!r}")
        self.remove_if_present(scenario.__class__)
        self._scenarios.append(scenario)

    def remove(self, scenario: ScenarioBase) -> None:
        assert isinstance(scenario, ScenarioBase)
        logger.info(f"Scenario: Remove {scenario!r}")
        self._scenarios.remove(scenario)

    def find(self, cls_scenario: Type[TScenario]) -> TScenario | None:
        """
        Return a scenario.
        None if scenario is not present
        """
        for scenario in self._scenarios:
            if scenario.__class__ is cls_scenario:
                return scenario
        return None

    def remove_if_present(self, cls_scenario: Type[TScenario]) -> bool:
        """
        Return True if the scenario was present
        """
        scenario = self.find(cls_scenario=cls_scenario)
        if scenario is None:
            return False
        self._scenarios.remove(scenario)
        return True

    @property
    def is_empty(self) -> bool:
        return len(self._scenarios) == 0

    def is_present(self, cls_scenario: Type[TScenario]) -> bool:
        """
        Return True if the scenario was present
        """
        scenario = self.find(cls_scenario=cls_scenario)
        if scenario is None:
            return False

        logger.info(f"Scenario: Apply {scenario!r}")
        scenario.decrement()
        return True

    def iter_by_class_haus(self, cls_scenario: Type[TScenario], haus: "Haus") -> Iterator[ScenarioBase]:
        from zentral.config_base import Haus

        assert isinstance(haus, Haus)
        for scenario in self._scenarios:
            if scenario.__class__ is cls_scenario:
                if scenario.haus_nummer is haus.config_haus.nummer:
                    logger.info(f"Scenario: Apply {scenario!r}")
                    scenario.decrement()
                    yield scenario


def ssh_repl_scenarios_history_add(f: io.TextIOBase, hausnummern: List[int]) -> None:
    examples = []
    for scenario_cls in SCENARIO_CLASSES:
        scenario: ScenarioBase = scenario_cls()
        scenario.fix_haus_nummer(hausnummern[0])
        examples.append(scenario.repl_example)

    for example in examples:
        f.write(f"#\n+{example}\n")


def ssh_repl_update_scenarios(repl_globals: Dict[str, Any], hausnummern: List[int]) -> None:
    def scenario_add(scenario: ScenarioBase) -> None:
        scenario.assert_valid_hausnummer(hausnummern=hausnummern)
        SCENARIOS.add(scenario)

    repl_globals[_FUNC_SCENARIO_ADD] = scenario_add

    for cls_scenario in SCENARIO_CLASSES:
        repl_globals[cls_scenario.__name__] = cls_scenario


SCENARIOS = Scenarios()
SCENARIO_CLASSES = []


@dataclasses.dataclass
class ScenarioClearScenarios(ScenarioBase):
    pass


@dataclasses.dataclass
class ScenarioHausModbusError(ScenarioBase):
    haus_nummer: int = 13
    counter: int = 1


@dataclasses.dataclass
class ScenarioHausPicoRebootReset(ScenarioBase):
    haus_nummer: int = 13
    counter: int = 1
    """
    """


@dataclasses.dataclass
class ScenarioHausModbusWrongRegisterCount(ScenarioBase):
    haus_nummer: int = 13
    counter: int = 1


@dataclasses.dataclass
class ScenarioHausModbusException(ScenarioBase):
    haus_nummer: int = 13
    counter: int = 60
    """
    After 60 exceptions, hsm dezentral will change to "error_lost"
    """


@dataclasses.dataclass
class ScenarioZentralDrehschalterManuell(ScenarioBase):
    duration_s: float = 10 * 60.0


@dataclasses.dataclass
class ScenarioHausModbusSystemExit(ScenarioBase):
    haus_nummer: int = 13


@dataclasses.dataclass
class ScenarioInfluxWriteCrazy(ScenarioBase):
    duration_s: float = 10 * 60.0


@dataclasses.dataclass
class ScenarioMischventilModbusSystemExit(ScenarioBase):
    pass


@dataclasses.dataclass
class ScenarioHausSpTemperatureIncrease(ScenarioBase):
    haus_nummer: int = 13
    position: SpPosition = SpPosition.MITTE
    delta_C: float = 5.0
    duration_s: float = 20.0

    def __post_init__(self):
        self.position = ensure_enum(SpPosition, self.position)


@dataclasses.dataclass
class ScenarioHausSpDs18Broken(ScenarioBase):
    haus_nummer: int = 13
    ds18_index: DS18Index = DS18Index.UNTEN_A
    ds18_ok_percent: int = 15
    duration_s: float = 20.0

    def __post_init__(self):
        self.ds18_index = ensure_enum(DS18Index, self.ds18_index)


@dataclasses.dataclass
class ScenarioOverwriteMischventil(ScenarioBase):
    duration_s: float = 10 * 60.0
    stellwert_100: float = 0


@dataclasses.dataclass
class ScenarioOverwriteRelais6PumpeEin(ScenarioBase):
    duration_s: float = 10 * 60.0
    pumpe_ein: bool = False


@dataclasses.dataclass
class ScenarioOverwriteRelais0Automatik(ScenarioBase):
    duration_s: float = 10 * 60.0
    automatik: bool = False


def register_scenarios() -> None:
    for name, scenario_cls in inspect.getmembers(sys.modules[__name__]):
        if not name.startswith("Scenario"):
            continue
        if not inspect.isclass(scenario_cls):
            continue
        if not issubclass(scenario_cls, ScenarioBase):
            continue
        if scenario_cls is ScenarioBase:
            continue

        SCENARIO_CLASSES.append(scenario_cls)


register_scenarios()
