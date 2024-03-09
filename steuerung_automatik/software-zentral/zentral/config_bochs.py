"""
"""

from zentral.config_base import ConfigEtappe, ConfigHaus, Haus
from zentral.constants import ETAPPE_TAG_PUENT, ETAPPE_TAG_BOCHS


ONLY_13 = False


def create_config_bochs() -> ConfigEtappe:
    config = ConfigEtappe(tag=ETAPPE_TAG_BOCHS, name="Bochseln")

    if ONLY_13:
        Haus(
            config_haus=ConfigHaus(
                nummer=13,
                addresse="Zelglistrasse 49",
                bewohner="Peter Märki und Sonja Rota",
                bauetappe=config,
            )
        )

    else:
        for nummer in range(1, 28):
            Haus(
                config_haus=ConfigHaus(
                    nummer=nummer,
                    addresse=f"Zelglistrasse x{nummer}",
                    bewohner="Hans und Peter Muster",
                    bauetappe=config,
                )
            )

    return config


def create_config_puent() -> ConfigEtappe:
    config = ConfigEtappe(tag=ETAPPE_TAG_PUENT, name="Puenterswis")
    return config


# print(f"{config_etappe_bochs.haeuser=}")
