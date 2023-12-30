"""
"""
from config_base import ConfigBauabschnitt, ConfigHaus, Haus

config_bauabschnitt_bochs = ConfigBauabschnitt(name="Bochseln")
config_bauabschnitt_puent = ConfigBauabschnitt(name="Punterswis")

Haus(
    config_haus=ConfigHaus(
        nummer=1,
        modbus_client_id=64,
        addresse="Zelglistrasse 26",
        bewohner="Peter Märki und Sonja Rota",
        bauabschnitt=config_bauabschnitt_bochs,
    )
)
Haus(
    config_haus=ConfigHaus(
        nummer=2,
        modbus_client_id=65,
        addresse="Zelglistrasse 28",
        bewohner="Hans Muster",
        bauabschnitt=config_bauabschnitt_bochs,
    )
)

print(f"{config_bauabschnitt_bochs.haeuser=}")
