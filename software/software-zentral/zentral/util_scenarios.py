import abc
import dataclasses
import enum
import inspect
import io
import logging
import sys
import time
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Type, TypeVar

from zentral.util_constants_haus import DS18Index, SpPosition, ensure_enum
from zentral.util_modulation_soll import BrennerNum, Modulation

if TYPE_CHECKING:
    from zentral.config_base import Haus
    from zentral.context import Context


logger = logging.getLogger(__name__)

_FUNC_SCENARIO_ADD = "scenario_add"


class ScenarioBase(abc.ABC):
    def __init__(self) -> None:
        self.duration_s: float
        self.counter: int

    def decrement(self) -> None:
        # pylint: disable=no-member
        # pylint: disable=attribute-defined-outside-init
        # pylint: disable=access-member-before-definition
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
        # pylint: disable=attribute-defined-outside-init  # W0201: Attribute 'haus_nummer' defined outside __init__ (attribute-defined-outside-init)
        self.haus_nummer = haus_nummer


TScenario = TypeVar("TScenario", bound=ScenarioBase)


class Scenarios:
    def __init__(self) -> None:
        self._scenarios: List[ScenarioBase] = []

    def add(self, ctx: "Optional[Context]", scenario: ScenarioBase) -> None:
        assert isinstance(scenario, ScenarioBase)

        if isinstance(scenario, ScenarioClearScenarios):
            logger.info("Scenario: Clear")
            self._scenarios.clear()
            return

        if hasattr(scenario, "action"):
            func_action = getattr(scenario, "action")
            logger.info(f"Scenario: {scenario!r}: Execute 'action()'")
            func_action(ctx=ctx)
            return

        logger.info(f"Scenario: Add {scenario!r}")
        # self.remove_if_present(scenario.__class__)
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
                scenario.decrement()
                return scenario  # type: ignore
        return None

    def find_and_remove(self, cls_scenario: Type[TScenario]) -> TScenario | None:
        scenario = self.find(cls_scenario=cls_scenario)
        if scenario is not None:
            self._scenarios.remove(scenario)
        return scenario

    def remove_if_present(self, cls_scenario: Type[TScenario]) -> bool:
        """
        Return True if the scenario was present
        """
        scenario = self.find_and_remove(cls_scenario=cls_scenario)
        return scenario is not None

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

        logger.debug(f"Scenario: Apply {scenario!r}")
        return True

    def iter_by_class(self, cls_scenario: Type[TScenario]) -> Iterator[TScenario]:
        for scenario in self._scenarios:
            if scenario.__class__ is cls_scenario:
                logger.debug(f"Scenario: Apply {scenario!r}")
                scenario.decrement()
                yield scenario  # type: ignore[misc]

    def iter_by_class_haus(self, cls_scenario: Type[TScenario], haus: "Haus") -> Iterator[TScenario]:
        from zentral.config_base import Haus

        assert isinstance(haus, Haus)
        for scenario in self._scenarios:
            if scenario.__class__ is cls_scenario:
                if scenario.haus_nummer is haus.config_haus.nummer:
                    logger.debug(f"Scenario: Apply {scenario!r}")
                    scenario.decrement()
                    yield scenario  # type: ignore[misc]


def ssh_repl_scenarios_history_add(f: io.TextIOBase, hausnummern: List[int]) -> None:
    examples = []
    for scenario_cls in SCENARIO_CLASSES:
        scenario: ScenarioBase = scenario_cls()
        scenario.fix_haus_nummer(hausnummern[0])
        examples.append(scenario.repl_example)

    for example in examples:
        f.write(f"#\n+{example}\n")


def ssh_repl_update_scenarios(repl_globals: Dict[str, Any], hausnummern: List[int]) -> None:
    ctx = repl_globals.get("ctx", None)

    def scenario_add(scenario: ScenarioBase) -> None:
        scenario.assert_valid_hausnummer(hausnummern=hausnummern)
        SCENARIOS.add(ctx=ctx, scenario=scenario)

    repl_globals[_FUNC_SCENARIO_ADD] = scenario_add

    for cls_scenario in SCENARIO_CLASSES:
        repl_globals[cls_scenario.__name__] = cls_scenario


SCENARIOS = Scenarios()
SCENARIO_CLASSES = []


@dataclasses.dataclass
class ScenarioClearScenarios(ScenarioBase):
    pass


@dataclasses.dataclass
class ScenarioHausModbusNoResponseReceived(ScenarioBase):
    haus_nummer: int = 13
    duration_s: float = 20.0


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
class ScenarioHausValveOpenCloseOthers(ScenarioBase):
    haus_nummer: int = 13
    duration_s: float = 20.0
    """
    """


@dataclasses.dataclass
class ScenarioHaeuserValveOpen(ScenarioBase):
    duration_s: float = 20.0
    """
    """


@dataclasses.dataclass
class ScenarioMasterValveOpenIterator(ScenarioBase):
    duration_haus_s: float = 180.0
    haeuser_count: int = 999

    def action(self, ctx: "Context") -> None:
        """
        Predefined method name 'action': Will be called automatically.
        """
        logger.info(f"Action: duration_haus_s={self.duration_haus_s:0.1f} haeuser_count={self.haeuser_count}")
        ctx.hsm_zentral.set_controller_master_valve_open_iterator(scenario=self)


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
class ScenarioHausModbusSystemExit(ScenarioBase):
    haus_nummer: int = 13


@dataclasses.dataclass
class ScenarioMBusReadInterval(ScenarioBase):
    duration_s: float = 10 * 60.0
    sleep_s: float = 60.0


@dataclasses.dataclass
class ScenarioInfluxWriteCrazy(ScenarioBase):
    duration_s: float = 10 * 60.0


@dataclasses.dataclass
class ScenarioMischventilModbusSystemExit(ScenarioBase):
    pass


@dataclasses.dataclass
class ScenarioMischventilModbusNoResponseReceived(ScenarioBase):
    duration_s: float = 20.0


@dataclasses.dataclass
class ScenarioHausSpTemperatureIncrease(ScenarioBase):
    """
    Real situation simulated:
     * The temperature of a DS18 pair incremented.
     * This might be usefull, to force start heating

    Notes:
     * duration_s should be longer than 60s, otherwise it may be swallowed.
     * Ony one class at the time may be active (as with all scenarios)

    Tested: 2024-07-27
    """

    haus_nummer: int = 13
    position: SpPosition = SpPosition.OBEN
    delta_C: float = -10.0
    duration_s: float = 20.0

    def __post_init__(self):
        self.position = ensure_enum(SpPosition, self.position)


@dataclasses.dataclass
class ScenarioHausSpTemperatureDiscrepancy(ScenarioBase):
    """
    If two sensors of a DX18Pair measures a difference of more 5C (DS18_REDUNDANCY_ACCEPTABLE_DIFF_C)
    then the result will be 'is_ok=False'.
    'error_C' in this case will be 10C (DS18_REDUNDANCY_ERROR_DIFF_C)

    Real situation simulated:
     * A DS18 pair measures different temperatures.
     * Grafana: "DS18 error_C"

    Notes:
     * duration_s should be longer than 60s, otherwise it may be swallowed.
     * Ony one class at the time may be active (as with all scenarios)

    Tested: 2024-07-27
    """

    haus_nummer: int = 13
    ds18_index: DS18Index = DS18Index.UNTEN_A
    discrepancy_C: float = 20.0
    duration_s: float = 120.0

    def __post_init__(self):
        self.ds18_index = ensure_enum(DS18Index, self.ds18_index)


@dataclasses.dataclass
class ScenarioHausSpDs18PercentOk(ScenarioBase):
    """
    Real situation simulated:
     * A DS18 is disconnected/shortened: Now 'ds18_op_percent' moves from 100% town to 0%.
     * Grafana: "DS18 onewire ok_percent"

    Notes:
     * duration_s should be longer than 60s, otherwise it may be swallowed.
     * Ony one class at the time may be active (as with all scenarios)

    Tested: 2024-07-27
    """

    haus_nummer: int = 13
    ds18_index: DS18Index = DS18Index.UNTEN_A
    ds18_ok_percent: int = 15
    duration_s: float = 120.0

    def __post_init__(self):
        self.ds18_index = ensure_enum(DS18Index, self.ds18_index)


@dataclasses.dataclass
class ScenarioOverwriteMischventil(ScenarioBase):
    duration_s: float = 10 * 60.0
    stellwert_100: float = 0


@dataclasses.dataclass
class ScenarioControllerPlusEinHaus(ScenarioBase):
    pass


@dataclasses.dataclass
class ScenarioControllerMinusEinHaus(ScenarioBase):
    pass


class LogLevel(enum.StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogModule(enum.StrEnum):
    controller_mischventil = "zentral.controller_mischventil"
    controller_mischventil_simple = "zentral.controller_mischventil_simple"
    zentral_controller_oekofen = "zentral.controller_oekofen"
    util_mbus = "zentral.util_mbus.py"
    util_scenarios = "zentral.util_scenarios"
    pymodbus_logging = "pymodbus.logging"
    asyncssd = "asyncssh"


@dataclasses.dataclass
class ScenarioSetLogLevel(ScenarioBase):
    module: LogModule = LogModule.controller_mischventil
    level: LogLevel = LogLevel.INFO

    def action(self, ctx: "Context") -> None:
        """
        Predefined method name 'action': Will be called automatically.
        """
        logger.info(f"Action: module={self.module} level={self.level}")
        logging.getLogger(self.module.value).setLevel(self.level.value)


class ActionTimerEnum(enum.StrEnum):
    LAST = "last"
    PUMPE_PWM = "pumpe_pwm"
    PUMPE_AUS_ZU_KALT = "pumpe_aus_zu_kalt"
    BRENNER_MODULATION_SOLL = "brenner_modulation_soll"
    ZWEITER_BRENNER_SPERRZEIT = "zweiter_brenner_sperrzeit"
    BRENNER_1_BURNOUT = "brenner_1_burnout"
    BRENNER_2_BURNOUT = "brenner_2_burnout"
    BRENNER_1_ERROR = "brenner_1_error"
    BRENNER_2_ERROR = "brenner_2_error"


@dataclasses.dataclass
class ScenarioActionTimerTimeOver(ScenarioBase):
    actiontimer: ActionTimerEnum = ActionTimerEnum.LAST

    def action(self, ctx: "Context") -> None:
        """
        Predefined method name 'action': Will be called automatically.
        """
        from zentral.controller_master import ControllerMaster
        from zentral.util_action import ActionTimer

        logger.info(f"Action: actiontimer={self.actiontimer}")
        controller_master: ControllerMaster = ctx.hsm_zentral.controller_master
        actiontimer: ActionTimer = {
            ActionTimerEnum.LAST: controller_master.handler_last.actiontimer,
            ActionTimerEnum.PUMPE_PWM: controller_master.handler_pumpe._actiontimer_pwm,
            ActionTimerEnum.PUMPE_AUS_ZU_KALT: controller_master.handler_pumpe._actiontimer_pumpe_aus_zu_kalt,
            ActionTimerEnum.BRENNER_MODULATION_SOLL: controller_master.handler_oekofen.modulation_soll.actiontimer,
            ActionTimerEnum.ZWEITER_BRENNER_SPERRZEIT: controller_master.handler_oekofen.modulation_soll.actiontimer_zweiter_brenner_sperrzeit,
            ActionTimerEnum.BRENNER_1_BURNOUT: controller_master.handler_oekofen.modulation_soll.zwei_brenner[0].burnout.actiontimer,
            ActionTimerEnum.BRENNER_2_BURNOUT: controller_master.handler_oekofen.modulation_soll.zwei_brenner[1].burnout.actiontimer,
            ActionTimerEnum.BRENNER_1_ERROR: controller_master.handler_oekofen.modulation_soll.zwei_brenner[0].actiontimer_error,
            ActionTimerEnum.BRENNER_2_ERROR: controller_master.handler_oekofen.modulation_soll.zwei_brenner[1].actiontimer_error,
        }[self.actiontimer]
        actiontimer.set_is_over()


@dataclasses.dataclass
class ScenarioSetRelais1bis5(ScenarioBase):
    duration_s: float = 10 * 60.0
    relais_1_elektro_notheizung: bool = False
    relais_2_brenner1_sperren: bool = False
    relais_3_brenner1_anforderung: bool = False
    relais_4_brenner2_sperren: bool = False
    relais_5_brenner2_anforderung: bool = False


@dataclasses.dataclass
class ScenarioOverwriteRelais6PumpeGesperrt(ScenarioBase):
    duration_s: float = 10 * 60.0
    pumpe_gesperrt: bool = False


@dataclasses.dataclass
class ScenarioOverwriteRelais0Automatik(ScenarioBase):
    duration_s: float = 10 * 60.0
    automatik: bool = False


class OekofenRegister(enum.StrEnum):
    EXTERNAL_CASCADE_CONTR = "EXTERNAL_CASCADE_CONTR"
    CASCADE_SET_C = "CASCADE_SET_C"
    # read only:
    #   CASCADE_ON_TEMP_C = "CASCADE_ON_TEMP_C"
    #   CASCADE_OFF_TEMP_C = "CASCADE_OFF_TEMP_C"
    FA1_MODE = "FA1_MODE"
    FA2_MODE = "FA2_MODE"
    FA1_TEMP_SET_C = "FA1_TEMP_SET_C"
    FA2_TEMP_SET_C = "FA2_TEMP_SET_C"
    FA1_REGEL_TEMP_C = "FA1_REGEL_TEMP_C"
    FA2_REGEL_TEMP_C = "FA2_REGEL_TEMP_C"
    FA1_POWER_kW = "FA1_POWER_kW"
    FA2_POWER_kW = "FA2_POWER_kW"

@dataclasses.dataclass
class ScenarioOekofenRegister(ScenarioBase):
    name: OekofenRegister = OekofenRegister.EXTERNAL_CASCADE_CONTR
    # name: str = "EXTERNAL_CASCADE_CONTR"
    value: float = 0.0


@dataclasses.dataclass
class ScenarioOekofenBrennerModulation(ScenarioBase):
    brenner_idx0: BrennerNum = BrennerNum.BRENNER_1
    modulation: Modulation = Modulation.MIN

    def action(self, ctx: "Context") -> None:
        """
        Predefined method name 'action': Will be called automatically.
        """
        ctx.hsm_zentral.controller_master.handler_oekofen.set_modulation(brenner_num=self.brenner_idx0, modulation=self.modulation)


@dataclasses.dataclass
class ScenarioOekofenBrennerStoerung(ScenarioBase):
    duration_s: float = 5 * 60.0
    brenner_idx0: BrennerNum = BrennerNum.BRENNER_1


@dataclasses.dataclass
class ScenarioOekofenModbusNoResponseReceived(ScenarioBase):
    duration_s: float = 120.0


@dataclasses.dataclass
class ScenarioZentralDrehschalterManuell(ScenarioBase):
    duration_s: float = 10 * 60.0


@dataclasses.dataclass
class ScenarioZentralSolltemperatur(ScenarioBase):
    solltemperature_Tfv_C: float = 65.0


@dataclasses.dataclass
class ScenarioZentralLastHandler(ScenarioBase):
    target_valve_open_count: int = 2

    def action(self, ctx: "Context") -> None:
        """
        Predefined method name 'action': Will be called automatically.
        """
        ctx.hsm_zentral.controller_master.handler_last.target_valve_open_count = self.target_valve_open_count


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

SCENARIOS.add(ctx=None, scenario=ScenarioInfluxWriteCrazy(duration_s=5 * 60.0))
