"""
"""
from config_base import ConfigBauetappe, ConfigHaus, Haus

config_bauabschnitt_bochs = ConfigBauetappe(name="Bochseln")
config_bauabschnitt_puent = ConfigBauetappe(name="Puenterswis")

Haus(
    config_haus=ConfigHaus(
        nummer=1,
        modbus_client_id=64,  # 0x40
        addresse="Zelglistrasse 26",
        bewohner="Peter Märki und Sonja Rota",
        bauetappe=config_bauabschnitt_bochs,
    )
)
# Haus(
#     config_haus=ConfigHaus(
#         nummer=2,
#         modbus_client_id=65,
#         addresse="Zelglistrasse 28",
#         bewohner="Hans Muster",
#         bauetappe=config_bauabschnitt_bochs,
#     )
# )

print(f"{config_bauabschnitt_bochs.haeuser=}")
