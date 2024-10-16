""" """

from utils_common.utils_constants import ZERO_BOCHS, ZERO_PUENT, ZERO_VIRGIN, ZEROES

from zentral.config_base import ConfigEtappe, ConfigHaus, Haus
from zentral.constants import ETAPPE_TAG_BOCHS, ETAPPE_TAG_PUENT, ETAPPE_TAG_VIRGIN
from zentral.util_fernleitung import Hausreihen


def create_hausreihen_puent() -> Hausreihen:
    h = Hausreihen()
    h.add("D", grafana=1, wasser_kg=0.0)
    h.add("E", grafana=2, wasser_kg=32.0)
    h.add("F", grafana=3, wasser_kg=38.0)
    h.add("G", grafana=4, wasser_kg=25.0)
    h["E"].einspeisung = h["D"]
    h["F"].einspeisung = h["D"]
    h["G"].einspeisung = h["F"]
    return h


def create_hausreihen_bochs() -> Hausreihen:
    h = Hausreihen()
    h.add("D", grafana=3, wasser_kg=29.0)
    h.add("E", grafana=1, wasser_kg=0.0)
    h.add("F", grafana=2, wasser_kg=10.0)
    h["D"].einspeisung = h["E"]
    h["F"].einspeisung = h["E"]
    return h


def create_config_etappe(hostname: str) -> ConfigEtappe:
    etappe = _create_config_etappe(hostname=hostname)
    etappe.hausreihen.update_influx_reihe()
    return etappe


def _create_config_etappe(hostname: str) -> ConfigEtappe:
    assert hostname in ZEROES

    if hostname == ZERO_VIRGIN:
        hausreihen = create_hausreihen_puent()
        config = ConfigEtappe(tag=ETAPPE_TAG_VIRGIN, name="Virgin", hausreihen=hausreihen)
        Haus(
            config_haus=ConfigHaus(
                nummer=99,
                addresse="Zelglistrasse 99",
                bewohner="Peter Märki und Sonja Rota",
                etappe=config,
                mbus_address="830036752D2C400D",
                hausreihe=hausreihen["G"],
            )
        )
        return config

    if hostname == ZERO_BOCHS:
        hausreihen = create_hausreihen_bochs()
        config = ConfigEtappe(tag=ETAPPE_TAG_BOCHS, name="Bochseln", hausreihen=hausreihen)
        for hausreihe, nummer, mbus_address in (
            ("D", 16, "83003678"),
            ("D", 17, "83003664"),
            ("D", 18, "83003682"),
            ("D", 19, "83003681"),
            ("E", 20, "83003671"),
            ("E", 21, "83003665"),
            ("E", 22, "83003670"),
            ("F", 23, "83003667"),
            ("F", 24, "83003666"),
            ("F", 25, "83003668"),
            ("F", 26, "83003669"),
        ):
            Haus(
                config_haus=ConfigHaus(
                    nummer=nummer,
                    addresse=f"Zelglistrasse x{nummer}",
                    bewohner="Hans und Peter Muster",
                    etappe=config,
                    mbus_address=mbus_address,
                    hausreihe=hausreihen[hausreihe],
                )
            )

        return config

    assert hostname == ZERO_PUENT
    hausreihen = create_hausreihen_puent()
    config = ConfigEtappe(tag=ETAPPE_TAG_PUENT, name="Puenterswis", hausreihen=hausreihen)
    for hausreihe, nummer, mbus_address in (
        ("D", 1, "83003680"),
        ("D", 2, "83003673"),
        ("D", 3, "83003683"),  # Falsch von Peter Schär: "83003663"
        ("D", 4, "83003672"),
        ("E", 5, "83003677"),
        ("E", 6, "83003679"),
        ("E", 7, "83003676"),
        ("F", 8, "82969016"),
        ("F", 9, "82969017"),
        ("F", 10, "82969010"),
        ("F", 11, "82969012"),
        ("G", 12, "83003674"),
        ("G", 13, "83003675"),
        ("G", 14, "82969015"),
        ("G", 15, "82969011"),
    ):
        Haus(
            config_haus=ConfigHaus(
                nummer=nummer,
                addresse=f"Zelglistrasse x{nummer}",
                bewohner="Hans und Peter Muster",
                etappe=config,
                mbus_address=mbus_address,
                hausreihe=hausreihen[hausreihe],
            )
        )

    return config
