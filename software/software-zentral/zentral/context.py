import asyncio
import logging
import os
import signal
import typing

from zentral import util_ssh_repl
from zentral.config_base import ConfigEtappe
from zentral.constants import DIRECTORY_LOG
from zentral.hsm_zentral import HsmZentral
from zentral.util_history_verbrauch_haus import INTERVAL_VERBRAUCH_HAUS_S
from zentral.util_influx import HsmDezentralInfluxLogger, HsmZentralInfluxLogger, Influx
from zentral.util_modbus_communication import ModbusCommunication
from zentral.util_modbus_exception import exception_handler_and_exit
from zentral.util_persistence_legionellen import PersistenceLegionellen
from zentral.util_scenarios import SCENARIOS, ScenarioInfluxWriteCrazy, ssh_repl_update_scenarios

logger = logging.getLogger(__name__)


ASYNCIO_TASK_HSM_DEZENTRAL_S = 60.0


class Context:
    def __init__(self, config_etappe: ConfigEtappe):
        self.config_etappe = config_etappe
        self.modbus_communication = self._factory_modbus_communication()
        self.influx = Influx()
        self.hsm_zentral = HsmZentral(ctx=self)
        self.hsm_zentral.init()
        self.hsm_zentral.write_mermaid_md(DIRECTORY_LOG / f"statemachine_{self.hsm_zentral.__class__.__name__}.md")
        influx_logger = HsmZentralInfluxLogger(influx=self.influx, ctx=self)
        self.hsm_zentral.add_logger(hsm_logger=influx_logger)
        self._persistence_legionellen = PersistenceLegionellen(ctx=self)

        def sigterm_handler(_signo, _stack_frame) -> typing.NoReturn:
            logger.warning("Received SIGTERM. Cleaning up...")
            self.close_and_flush_influx()
            logger.warning("...done")
            os._exit(0)

        signal.signal(signal.SIGTERM, sigterm_handler)

    def _factory_modbus_communication(self) -> ModbusCommunication:
        return ModbusCommunication(self)

    def close_and_flush_influx(self) -> None:
        self.influx.close_and_flush()
        for haus in self.config_etappe.haeuser:
            if haus.status_haus is not None:
                haus.status_haus.hsm_dezentral.save_persistence(why="Exiting app")

        self._persistence_legionellen.save(force=True, why="Exiting app")

    async def init(self) -> None:
        self.config_etappe.init()

        for haus in self.config_etappe.haeuser:
            assert haus.status_haus is not None
            haus.status_haus.hsm_dezentral._context = self
            haus.status_haus.hsm_dezentral.init()

        # Add influx logger
        for haus in self.config_etappe.haeuser:
            influx_logger = HsmDezentralInfluxLogger(influx=self.influx, haus=haus)
            haus.status_haus.hsm_dezentral.add_logger(hsm_logger=influx_logger)

        # Start the statemachine.
        # This will already send message to influx
        self.hsm_zentral.start()
        for haus in self.config_etappe.haeuser:
            haus.status_haus.hsm_dezentral.start()

    async def create_ssh_repl(self) -> None:
        def influx_delete_bucket_virgin():
            _task = asyncio.create_task(self.influx.delete_bucket_virgin())

        repl_globals = dict(
            ctx=self,
            influx_delete_bucket_virgin=influx_delete_bucket_virgin,
        )
        hausnummern = self.config_etappe.hausnummern
        ssh_repl_update_scenarios(repl_globals=repl_globals, hausnummern=hausnummern)
        await util_ssh_repl.create(repl_globals=repl_globals, hausnummern=hausnummern)

    async def task_hsm(self) -> None:
        async def sleep(duration_s: float):
            # Sleep duration_s
            while duration_s > 0.0:
                await asyncio.sleep(2.0)
                duration_s -= 2.0
                if SCENARIOS.is_present(ScenarioInfluxWriteCrazy):
                    #  Sleep only 2s when a ScenarioInfluxWriteCrazy is active
                    return

        async with exception_handler_and_exit(ctx=self, task_name="hsm", exit_code=45):
            while True:
                for haus in self.config_etappe.haeuser:
                    assert haus.status_haus is not None
                    await self.influx.send_hsm_dezental(
                        haus=haus,
                        state=haus.status_haus.hsm_dezentral.get_state(),
                    )

                self._persistence_legionellen.update()

                await self.influx.send_hsm_zentral(ctx=self, state=self.hsm_zentral.get_state())

                await sleep(duration_s=ASYNCIO_TASK_HSM_DEZENTRAL_S)

    async def task_verbrauch(self) -> None:
        async with exception_handler_and_exit(ctx=self, task_name="verbrauch", exit_code=46):
            while True:
                for haus in self.config_etappe.haeuser:
                    assert haus.status_haus is not None
                    await haus.status_haus.hsm_dezentral.handle_history_verbrauch()

                await asyncio.sleep(INTERVAL_VERBRAUCH_HAUS_S / 100.0)

    async def __aenter__(self):
        await self.modbus_communication.connect()
        return self

    async def __aexit__(self, *exc):
        await self.modbus_communication.close()
        self.close_and_flush_influx()
        return False
