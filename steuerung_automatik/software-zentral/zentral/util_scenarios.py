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
from typing import List, Optional
import logging
from zentral import config_bochs

from zentral.config_base import Haus

logger = logging.getLogger(__name__)


class ScenarioBase(abc.ABC):
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

    def find_by_class_haus(self, cls_scenario, haus: Haus) -> Optional[ScenarioBase]:
        assert isinstance(haus, Haus)
        for scenario in self._scenarios:
            if scenario.__class__ is cls_scenario:
                if scenario.haus_nummer.value is haus.config_haus.nummer:
                    return scenario
        # raise KeyError(
        #     f"Scenario of class {cls_scenario.__name__} and haus {haus.config_haus.nummer} not found!"
        # )
        return None


SCENARIOS = Scenarios()
SCENARIO_CLASSES = []


@dataclasses.dataclass(frozen=True)
class ScenarioHausModbusError(ScenarioBase):
    haus_nummer: config_bochs.config_bauabschnitt_bochs.haus_enum


SCENARIO_CLASSES.append(ScenarioHausModbusError)


@dataclasses.dataclass(frozen=True)
class ScenarioHausModbusWrongRegisterCount(ScenarioBase):
    haus_nummer: config_bochs.config_bauabschnitt_bochs.haus_enum


SCENARIO_CLASSES.append(ScenarioHausModbusWrongRegisterCount)


@dataclasses.dataclass(frozen=True)
class ScenarioHausModbusException(ScenarioBase):
    haus_nummer: config_bochs.config_bauabschnitt_bochs.haus_enum


SCENARIO_CLASSES.append(ScenarioHausModbusException)
