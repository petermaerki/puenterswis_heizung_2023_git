""" """

from utils_common.utils_constants import ZEROES, ZERO_VIRGIN, ZERO_BOCHS, ZERO_PUENT
from zentral.config_base import ConfigEtappe, ConfigHaus, Haus
from zentral.constants import ETAPPE_TAG_VIRGIN, ETAPPE_TAG_BOCHS, ETAPPE_TAG_PUENT

ONLY_13 = False


def create_config_etappe(hostname: str) -> ConfigEtappe:
    assert hostname in ZEROES

    if hostname == ZERO_VIRGIN:
        config = ConfigEtappe(tag=ETAPPE_TAG_VIRGIN, name="Virgin")
        Haus(
            config_haus=ConfigHaus(
                nummer=99,
                addresse="Zelglistrasse 99",
                bewohner="Peter Märki und Sonja Rota",
                etappe=config,
            )
        )
        return config

    if ONLY_13:
        config = ConfigEtappe(tag=ETAPPE_TAG_VIRGIN, name="Virgin")
        Haus(
            config_haus=ConfigHaus(
                nummer=13,
                addresse="Zelglistrasse 49",
                bewohner="Peter Märki und Sonja Rota",
                etappe=config,
            )
        )
        return config

    if hostname == ZERO_BOCHS:
        config = ConfigEtappe(tag=ETAPPE_TAG_BOCHS, name="Bochseln")
        for nummer in range(16, 26 + 1):
            Haus(
                config_haus=ConfigHaus(
                    nummer=nummer,
                    addresse=f"Zelglistrasse x{nummer}",
                    bewohner="Hans und Peter Muster",
                    etappe=config,
                )
            )

        return config

    assert hostname == ZERO_PUENT
    config = ConfigEtappe(tag=ETAPPE_TAG_PUENT, name="Puenterswis")
    for nummer in range(1, 15 + 1):
        Haus(
            config_haus=ConfigHaus(
                nummer=nummer,
                addresse=f"Zelglistrasse x{nummer}",
                bewohner="Hans und Peter Muster",
                etappe=config,
            )
        )

    return config


def create_config_puent() -> ConfigEtappe:
    config = ConfigEtappe(tag=ETAPPE_TAG_PUENT, name="Puenterswis")
    return config


# print(f"{config_etappe_bochs.haeuser=}")
