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

import abc
import dataclasses
from typing import Iterator, List, TYPE_CHECKING
import logging

from zentral.util_constants_haus import DS18Index, SpPosition

if TYPE_CHECKING:
    from zentral.config_base import Haus

logger = logging.getLogger(__name__)


class ScenarioBase(abc.ABC):
    def decrement(self) -> None:
        if not hasattr(self, "counter"):
            return

        self.counter -= 1
        if self.counter <= 0:
            self.destroy()

    def destroy(self) -> None:
        SCENARIOS.remove(self)


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
        self._scenarios.append(scenario)

    def remove(self, scenario: ScenarioBase) -> None:
        assert isinstance(scenario, ScenarioBase)
        logger.info(f"Scenario: Remove {scenario!r}")
        self._scenarios.remove(scenario)

    def remove_if_present(self, cls_scenario) -> bool:
        """
        Return True if the scenario was present
        """
        for scenario in self._scenarios:
            if scenario.__class__ is cls_scenario:
                self._scenarios.remove(scenario)
                return True
        return False

    def iter_by_class_haus(self, cls_scenario, haus: "Haus") -> Iterator[ScenarioBase]:
        from zentral.config_base import Haus

        assert isinstance(haus, Haus)
        for scenario in self._scenarios:
            if scenario.__class__ is cls_scenario:
                if scenario.haus_nummer is haus.config_haus.nummer:
                    scenario.decrement()
                    yield scenario


SCENARIOS = Scenarios()
SCENARIO_CLASSES = []


@dataclasses.dataclass
class ScenarioClearScenarios(ScenarioBase):
    pass


SCENARIO_CLASSES.append(ScenarioClearScenarios)


@dataclasses.dataclass
class ScenarioHausModbusError(ScenarioBase):
    haus_nummer: int = 13
    counter: int = 1


SCENARIO_CLASSES.append(ScenarioHausModbusError)


@dataclasses.dataclass
class ScenarioHausPicoRebootReset(ScenarioBase):
    haus_nummer: int = 13
    counter: int = 1
    """
    """


SCENARIO_CLASSES.append(ScenarioHausPicoRebootReset)


@dataclasses.dataclass
class ScenarioHausModbusWrongRegisterCount(ScenarioBase):
    haus_nummer: int = 13
    counter: int = 1


SCENARIO_CLASSES.append(ScenarioHausModbusWrongRegisterCount)


@dataclasses.dataclass
class ScenarioHausModbusException(ScenarioBase):
    haus_nummer: int = 13
    counter: int = 60
    """
    After 50 exceptions, hsm dezentral will change to "error_lost"
    """


SCENARIO_CLASSES.append(ScenarioHausModbusException)


@dataclasses.dataclass
class ScenarioHausModbusSystemExit(ScenarioBase):
    haus_nummer: int = 13


SCENARIO_CLASSES.append(ScenarioHausModbusSystemExit)


@dataclasses.dataclass
class ScenarioMischventilModbusSystemExit(ScenarioBase):
    pass


SCENARIO_CLASSES.append(ScenarioMischventilModbusSystemExit)


@dataclasses.dataclass
class ScenarioHausSpTemperatureIncrease(ScenarioBase):
    haus_nummer: int = 13
    position: SpPosition = SpPosition.OBEN
    delta_C: float = 5.0
    counter: int = 1


SCENARIO_CLASSES.append(ScenarioHausSpTemperatureIncrease)


@dataclasses.dataclass
class ScenarioHausSpDs18Broken(ScenarioBase):
    haus_nummer: int = 13
    ds18_index: DS18Index = DS18Index.UNTEN_A
    ds18_ok_percent: int = 15
    counter: int = 1


SCENARIO_CLASSES.append(ScenarioHausSpDs18Broken)
