"""
"""

from zentral.config_base import ConfigEtappe, ConfigHaus, Haus
from zentral.constants import ETAPPE_TAG_PUENT, ETAPPE_TAG_BOCHS


def create_config_bochs() -> ConfigEtappe:
    config = ConfigEtappe(tag=ETAPPE_TAG_BOCHS, name="Bochseln")

    Haus(
        config_haus=ConfigHaus(
            nummer=12,
            addresse="Zelglistrasse 47",
            bewohner="Nicole S.",
            bauetappe=config,
        )
    )
    Haus(
        config_haus=ConfigHaus(
            nummer=13,
            addresse="Zelglistrasse 49",
            bewohner="Peter Märki und Sonja Rota",
            bauetappe=config,
        )
    )
    return config


def create_config_puent() -> ConfigEtappe:
    config = ConfigEtappe(tag=ETAPPE_TAG_PUENT, name="Puenterswis")
    return config


# print(f"{config_etappe_bochs.haeuser=}")
