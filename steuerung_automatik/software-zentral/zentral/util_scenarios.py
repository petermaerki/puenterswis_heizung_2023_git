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
from enum import StrEnum
import dataclasses
from typing import List, Optional, TYPE_CHECKING
import logging

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
        logger.info(f"Scenario: Add {scenario!r}")
        self._scenarios.append(scenario)

    def remove(self, scenario: ScenarioBase) -> None:
        assert isinstance(scenario, ScenarioBase)
        logger.info(f"Scenario: Remove {scenario!r}")
        self._scenarios.remove(scenario)

    def find_by_scenario(self, scenario: ScenarioBase) -> ScenarioBase:
        repr_scenario = repr(scenario)
        for scenario in self._scenarios:
            if repr(scenario) == repr_scenario:
                return scenario
        raise KeyError(f"Scenario {scenario!r} not found!")

    def find_by_class(self, cls_scenario) -> ScenarioBase:
        for scenario in self._scenarios:
            if scenario.__class__ is cls_scenario:
                return scenario
        raise KeyError(f"Scenario of class {cls_scenario.__name__} not found!")

    def find_by_class_haus(self, cls_scenario, haus: "Haus") -> Optional[ScenarioBase]:
        from zentral.config_base import Haus

        assert isinstance(haus, Haus)
        for scenario in self._scenarios:
            if scenario.__class__ is cls_scenario:
                if scenario.haus_nummer is haus.config_haus.nummer:
                    scenario.decrement()
                    return scenario
        # raise KeyError(
        #     f"Scenario of class {cls_scenario.__name__} and haus {haus.config_haus.nummer} not found!"
        # )
        return None


SCENARIOS = Scenarios()
SCENARIO_CLASSES = []


@dataclasses.dataclass
class ScenarioHausModbusError(ScenarioBase):
    haus_nummer: int = 13
    counter: int = 1


SCENARIO_CLASSES.append(ScenarioHausModbusError)


@dataclasses.dataclass
class ScenarioHausModbusWrongRegisterCount(ScenarioBase):
    haus_nummer: int = 13
    counter: int = 1


SCENARIO_CLASSES.append(ScenarioHausModbusWrongRegisterCount)


@dataclasses.dataclass
class ScenarioHausModbusException(ScenarioBase):
    haus_nummer: int = 13
    counter: int = 1


SCENARIO_CLASSES.append(ScenarioHausModbusException)


class SpPosition(StrEnum):
    OBEN = "oben"
    MITTE = "mitte"
    UNTEN = "unten"


@dataclasses.dataclass
class ScenarioHausSpTemperatureIncrease(ScenarioBase):
    haus_nummer: int = 13
    position: SpPosition = SpPosition.OBEN
    delta_C: float = 5.0
    counter: int = 1


SCENARIO_CLASSES.append(ScenarioHausSpTemperatureIncrease)
