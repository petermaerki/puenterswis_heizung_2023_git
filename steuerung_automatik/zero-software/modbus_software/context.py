from modbus_software.config_base import ConfigBauabschnitt
from modbus_software.constants import DIRECTORY_LOG
from modbus_software.hsm_zentral import HsmZentral

from modbus_software.util_modbus_communication import ModbusCommunication


class Context:
    def __init__(self, config_bauabschnitt: ConfigBauabschnitt):
        self.config_bauabschnitt = config_bauabschnitt
        self.modbus_communication = ModbusCommunication(self)
        self.hsm_zentral = HsmZentral()
        self.hsm_zentral.init()
        self.hsm_zentral.write_mermaid_md(
            DIRECTORY_LOG / f"statemachine_{self.hsm_zentral.__class__.__name__}.md"
        )

        for config_haus in self.config_bauabschnitt.haeuser:
            config_haus.status_haus.hsm_dezentral.init()

        self.hsm_zentral.start()
        for config_haus in self.config_bauabschnitt.haeuser:
            config_haus.status_haus.hsm_dezentral.start()

    async def __aenter__(self):
        await self.modbus_communication.connect()
        return self

    async def __aexit__(self, *exc):
        self.modbus_communication.close()
        return False
