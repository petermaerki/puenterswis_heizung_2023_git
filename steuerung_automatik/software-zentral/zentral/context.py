from zentral.config_base import ConfigBauabschnitt
from zentral.constants import DIRECTORY_LOG
from zentral.hsm_zentral import HsmZentral

from zentral.util_modbus_communication import ModbusCommunication


class Context:
    def __init__(self, config_bauabschnitt: ConfigBauabschnitt):
        self.config_bauabschnitt = config_bauabschnitt
        self.modbus_communication = self._factory_modbus_communication()
        self.hsm_zentral = HsmZentral()
        self.hsm_zentral.init()
        self.hsm_zentral.write_mermaid_md(
            DIRECTORY_LOG / f"statemachine_{self.hsm_zentral.__class__.__name__}.md"
        )

        for haus in self.config_bauabschnitt.haeuser:
            haus.status_haus.hsm_dezentral.init()

        self.hsm_zentral.start()
        for haus in self.config_bauabschnitt.haeuser:
            haus.status_haus.hsm_dezentral.start()

    def _factory_modbus_communication(self) -> ModbusCommunication:
        return ModbusCommunication(self)

    async def __aenter__(self):
        await self.modbus_communication.connect()
        return self

    async def __aexit__(self, *exc):
        self.modbus_communication.close()
        return False
