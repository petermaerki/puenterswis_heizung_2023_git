import asyncio
from zentral.config_base import ConfigEtappe
from zentral.constants import DIRECTORY_LOG
from zentral.hsm_zentral import HsmZentral
from zentral.util_influx import Influx, HsmInfluxLogger

from zentral.util_modbus_communication import ModbusCommunication
from zentral.utils_logger import HsmLoggingLogger


class Context:
    def __init__(self, config_etappe: ConfigEtappe):
        self.config_etappe = config_etappe
        self.modbus_communication = self._factory_modbus_communication()
        self.hsm_zentral = HsmZentral(hsm_logger=HsmLoggingLogger("HsmZentral"))
        self.hsm_zentral.init()
        self.hsm_zentral.write_mermaid_md(DIRECTORY_LOG / f"statemachine_{self.hsm_zentral.__class__.__name__}.md")
        self.influx = Influx(etappe=self.config_etappe.tag)

    def _factory_modbus_communication(self) -> ModbusCommunication:
        return ModbusCommunication(self)

    async def init(self) -> None:
        if False:
            await self.influx.delete_bucket()

        self.config_etappe.init()

        for haus in self.config_etappe.haeuser:
            haus.status_haus.hsm_dezentral.init()

        # Add influx logger
        for haus in self.config_etappe.haeuser:
            influx_logger = HsmInfluxLogger(haus=haus, grafana=self.influx)
            haus.status_haus.hsm_dezentral.add_logger(hsm_logger=influx_logger)

        # Start the statemachine.
        # This will already send message to influx
        self.hsm_zentral.start()
        for haus in self.config_etappe.haeuser:
            haus.status_haus.hsm_dezentral.start()

    async def task_hsm(self) -> None:
        if True:
            while True:
                for haus in self.config_etappe.haeuser:
                    await self.influx.send_hsm_dezental(
                        haus=haus,
                        state=haus.status_haus.hsm_dezentral.get_state(),
                    )

                await asyncio.sleep(5)

    async def __aenter__(self):
        await self.modbus_communication.connect()
        return self

    async def __aexit__(self, *exc):
        await self.modbus_communication.close()
        await self.influx.close()
        return False
