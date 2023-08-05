from dataclasses import dataclass

from hsm_signal import HsmTimeSignal

from program.constants import DIRECTORY_DOC
from program.hsm_jahreszeit import HsmJahreszeit
from program.hsm_ladung import HsmLadung
from program.hsm_pumpe import HsmPumpe


@dataclass(repr=True)
class Sensoren:
    brenner_1_on: bool = False
    brenner_2_on: bool = False
    anforderung: bool = False
    zentralspeicher_oben_Tszo_C: float = 20.0
    # zentralspeicher_mitte_Tszm_C: float = 20.0
    # zentralspeicher_unten_Tszu_C: float = 20.0
    fernleitung_warm_Tfv_C: float = 30.0
    fernleitung_kalt_Tfr_C: float = 20.0
    aussentemperatur_Taussen_C = 15.0


class Konstanten:
    """Elfero Heizregler dezentral "Elesta RDO244A200 Art 163286
    Einstellen Warmwasser Solltemperatur: Pfeil nach unten druecken bis Thermometer und Wasserhahn: Warmwasser Solltemperatur. Diese ist normalerweise auf 45C.
    Einstellen Hysterese: Fachmannebene Parameter 191.
    """

    elfero_dezentral_solltemperatur_warmwasser_C = 45.0
    elfero_dezentral_hysterese_warmwasser_C = 10.0
    temperaturueberhoehung_solltemperatur_warmwasser_C = 5.0
    sommer_fernleitung_solltemperatur_C = (
        elfero_dezentral_solltemperatur_warmwasser_C
        + (elfero_dezentral_hysterese_warmwasser_C * 0.5)
        + temperaturueberhoehung_solltemperatur_warmwasser_C
    )

    _legionellen_normtemperatur_C = 55.0  # https://suissetec.ch/files/PDFs/Merkblaetter/Sanitaer/Deutsch/2021_10_MB_SIA_385_1_DE_Editierbar.pdf
    _legionellen_temperaturueberhoehung_C = 5.0  # Reserve, Fernleitung
    legionellen_fernleitungstemperatur_C = (
        _legionellen_normtemperatur_C + _legionellen_temperaturueberhoehung_C
    )

    @property
    def fernleitungs_solltemperatur_heizen_min_C(self):
        """Ferneitungstemperatur damit die Leistung uebertragen werden kann"""
        _waermekapazitaet_wasser_JkgK = 4190.0
        _nominalfluss_puent_kg_s = (
            2300.0 / 3600.0
        )  # Nominalfluss bei Zentrale gemaess Auslegung Gadola
        _maximalleistung_puent_W = 70000.0  # Maximalleistung Oekofen Puenterswis
        _temperaturspreizung_maximalleistung_K = _maximalleistung_puent_W / (
            _nominalfluss_puent_kg_s * _waermekapazitaet_wasser_JkgK
        )
        _aussentemperatur_grenze_heizbetrieb_C = 20.0
        _aussentemperatur_maximalleistung_C = -14.0
        _ruecklauf_bodenheizung_C = 24.0
        _umgebungstemperatur_todo_richtig_machen_C = 10.0
        # todo korrekte formel
        return 45.0  # todo


class Aktoren:
    pumpe_on: bool = False
    ventile_zwangsladung_on: bool = False


class Context:
    def __init__(self):
        self.hsm_ladung = HsmLadung(self)
        self.hsm_jahreszeit = HsmJahreszeit(self)
        self.hsm_pumpe = HsmPumpe(self)
        self.hsms = (self.hsm_ladung, self.hsm_jahreszeit, self.hsm_pumpe)
        self.sensoren = Sensoren()
        self.aktoren = Aktoren()

        for hsm in self.hsms:
            hsm.init()
            hsm.write_mermaid_md(
                DIRECTORY_DOC / f"statemachine_{hsm.__class__.__name__}.md"
            )

        for hsm in self.hsms:
            hsm.start()

    def dispatch(self, signal: HsmTimeSignal) -> None:
        for hsm in self.hsms:
            hsm.dispatch(signal)
