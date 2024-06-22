import asyncio

from zentral import util_ssh_repl
from zentral.config_base import ConfigEtappe
from zentral.constants import DIRECTORY_LOG
from zentral.hsm_zentral import HsmZentral
from zentral.util_influx import HsmDezentralInfluxLogger, HsmZentralInfluxLogger, Influx
from zentral.util_modbus_communication import ModbusCommunication
from zentral.util_scenarios import SCENARIOS, ScenarioInfluxWriteCrazy, ssh_repl_update_scenarios


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

    def _factory_modbus_communication(self) -> ModbusCommunication:
        return ModbusCommunication(self)

    async def close_and_flush_influx(self) -> None:
        await self.influx.close_and_flush()

    async def init(self) -> None:
        self.config_etappe.init()

        for haus in self.config_etappe.haeuser:
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

        while True:
            for haus in self.config_etappe.haeuser:
                await self.influx.send_hsm_dezental(
                    haus=haus,
                    state=haus.status_haus.hsm_dezentral.get_state(),
                )

            await self.influx.send_hsm_zentral(ctx=self, state=self.hsm_zentral.get_state())
            await sleep(duration_s=60.0)

    async def task_verbrauch(self) -> None:
        while True:
            for haus in self.config_etappe.haeuser:
                await haus.status_haus.hsm_dezentral.handle_history_verbrauch()

            await asyncio.sleep(60.0)

    async def __aenter__(self):
        await self.modbus_communication.connect()
        return self

    async def __aexit__(self, *exc):
        await self.modbus_communication.close()
        await self.influx.close_and_flush()
        return False
