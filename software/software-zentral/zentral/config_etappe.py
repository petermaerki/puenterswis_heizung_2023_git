""" """

from utils_common.utils_constants import ZERO_BOCHS, ZERO_PUENT, ZERO_VIRGIN, ZEROES

from zentral.config_base import ConfigEtappe, ConfigHaus, Haus
from zentral.constants import ETAPPE_TAG_BOCHS, ETAPPE_TAG_PUENT, ETAPPE_TAG_VIRGIN

ONLY_13 = False


def create_config_etappe(hostname: str) -> ConfigEtappe:
    assert hostname in ZEROES

    if hostname == ZERO_VIRGIN:
        config = ConfigEtappe(tag=ETAPPE_TAG_VIRGIN, name="Virgin")
        Haus(config_haus=ConfigHaus(nummer=99, addresse="Zelglistrasse 99", bewohner="Peter Märki und Sonja Rota", etappe=config, mbus_address="830036752D2C400D"))
        return config

    if ONLY_13:
        config = ConfigEtappe(tag=ETAPPE_TAG_VIRGIN, name="Virgin")
        Haus(
            config_haus=ConfigHaus(
                nummer=13,
                addresse="Zelglistrasse 49",
                bewohner="Peter Märki und Sonja Rota",
                etappe=config,
                mbus_address="830036752D2C400D",
            )
        )
        return config

    if hostname == ZERO_BOCHS:
        config = ConfigEtappe(tag=ETAPPE_TAG_BOCHS, name="Bochseln")
        for nummer, mbus_address in (
            (16, "83003678"),
            (17, "83003664"),
            (18, "83003682"),
            (19, "83003668"),
            (20, "83003671"),
            (21, "83003665"),
            (22, "83003670"),
            (23, "83003667"),
            (24, "83003666"),
            (25, "83003668"),
            (26, "83003669"),
        ):
            Haus(
                config_haus=ConfigHaus(
                    nummer=nummer,
                    addresse=f"Zelglistrasse x{nummer}",
                    bewohner="Hans und Peter Muster",
                    etappe=config,
                    mbus_address=mbus_address,
                )
            )

        return config

    assert hostname == ZERO_PUENT
    config = ConfigEtappe(tag=ETAPPE_TAG_PUENT, name="Puenterswis")
    for nummer, mbus_address in (
        (1, "83003680"),
        (2, "83003673"),
        (3, "83003683"),  # Falsch von Peter Schär: "83003663"
        (4, "83003672"),
        (5, "83003677"),
        (6, "83003679"),
        (7, "83003676"),
        (8, "82969016"),
        (9, "82969017"),
        (10, "82969010"),
        (11, "82969012"),
        (12, "83003674"),
        (13, "83003675"),
        (14, "82969015"),
        (15, "82969011"),
    ):
        Haus(
            config_haus=ConfigHaus(
                nummer=nummer,
                addresse=f"Zelglistrasse x{nummer}",
                bewohner="Hans und Peter Muster",
                etappe=config,
                mbus_address=mbus_address,
            )
        )

    return config


def create_config_puent() -> ConfigEtappe:
    config = ConfigEtappe(tag=ETAPPE_TAG_PUENT, name="Puenterswis")
    return config


# print(f"{config_etappe_bochs.haeuser=}")
