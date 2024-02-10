from zentral.config_base import ConfigEtappe
from zentral.constants import DIRECTORY_LOG
from zentral.hsm_zentral import HsmZentral
from zentral.util_influxdb import Grafana

from zentral.util_modbus_communication import ModbusCommunication


class Context:
    def __init__(self, config_etappe: ConfigEtappe):
        self.config_etappe = config_etappe
        self.modbus_communication = self._factory_modbus_communication()
        self.hsm_zentral = HsmZentral()
        self.hsm_zentral.init()
        self.hsm_zentral.write_mermaid_md(DIRECTORY_LOG / f"statemachine_{self.hsm_zentral.__class__.__name__}.md")
        self.grafana = Grafana(etappe=self.config_etappe.tag)

        for haus in self.config_etappe.haeuser:
            haus.status_haus.hsm_dezentral.init()

        self.hsm_zentral.start()
        for haus in self.config_etappe.haeuser:
            haus.status_haus.hsm_dezentral.start()

    def _factory_modbus_communication(self) -> ModbusCommunication:
        return ModbusCommunication(self)

    async def __aenter__(self):
        await self.modbus_communication.connect()
        return self

    async def __aexit__(self, *exc):
        await self.modbus_communication.close()
        await self.grafana.close()
        return False
