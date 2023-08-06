from dataclasses import dataclass

from program.constants import DIRECTORY_DOC
from program.hsm_jahreszeit import HsmJahreszeit
from program.hsm_ladung import HsmLadung
from program.hsm_legionellen import HsmLegionellen
from program.hsm_pumpe import HsmPumpe
from program.hsm_signal import SignalBase


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
    energie_heute_kWh = 0.0
    energie_gestern_kWh = 0.0


class Konstanten:
    def __init__(self):
        """
        Fernleitungstemperatur fuer eine Warmwasserladung damit die
        Anforderung vom Elferoregler erfuellt wird.
        Elfero Heizregler dezentral "Elesta RDO244A200 Art 163286
        Einstellen Warmwasser Solltemperatur: Pfeil nach unten druecken bis
        Thermometer und Wasserhahn: Warmwasser Solltemperatur.
        Diese ist normalerweise auf 45C.
        Einstellen Hysterese: Fachmannebene Parameter 191.
        """
        elfero_dezentral_solltemperatur_warmwasser_C = 45.0
        elfero_dezentral_hysterese_warmwasser_C = 10.0
        reserve_solltemperatur_warmwasser_C = 5.0

        self.sommer_fernleitung_solltemperatur_warmwasserladung_C = (
            elfero_dezentral_solltemperatur_warmwasser_C
            + (elfero_dezentral_hysterese_warmwasser_C * 0.5)
            + reserve_solltemperatur_warmwasser_C
        )

        """
        Fernleitungstemperatur damit die Legionellen in den
        dezentralen Speichern absterben
        """
        # https://suissetec.ch/files/PDFs/Merkblaetter/Sanitaer/Deutsch/2021_10_MB_SIA_385_1_DE_Editierbar.pdf
        legionellen_normtemperatur_C: float = 55.0
        # Reserve, Fernleitung
        legionellen_temperaturueberhoehung_C: float = 5.0

        self.legionellen_fernleitungstemperatur_C = (
            legionellen_normtemperatur_C + legionellen_temperaturueberhoehung_C
        )

        self.legionellen_intervall_s = (
            7 * 24 * 3600.0
        )  # eine Legionellenladung macht man typischweise jede Woche

        self.legionellen_zwangsladezeit_s = (
            5 * 3600.0
        )  # Zeit welche mindestens geladen werden muss

        # bochs = 0
        # puent = 1


class Aktoren:
    pumpe_on: bool = False
    ventile_zwangsladung_on: bool = False


class Context:
    def __init__(self):
        self.hsm_ladung = HsmLadung(self)
        self.hsm_jahreszeit = HsmJahreszeit(self)
        self.hsm_pumpe = HsmPumpe(self)
        self.hsm_legionellen = HsmLegionellen(self)
        self.hsms = (
            self.hsm_jahreszeit,
            self.hsm_ladung,
            self.hsm_pumpe,
            self.hsm_legionellen,
        )
        self.sensoren = Sensoren()
        self.aktoren = Aktoren()
        self.konstanten = Konstanten()
        self.time_s: float = 0.0

        for hsm in self.hsms:
            hsm.init()
            hsm.write_mermaid_md(
                DIRECTORY_DOC / f"statemachine_{hsm.__class__.__name__}.md"
            )

        for hsm in self.hsms:
            hsm.start()

    def dispatch(self, signal: SignalBase) -> None:
        for hsm in self.hsms:
            hsm.dispatch(signal)

    @property
    def fernleitungs_solltemperatur_C(self) -> float:
        """Fernleitungstemperatur damit die Heizleistung uebertragen werden kann"""
        waermekapazitaet_wasser_JkgK = 4190.0
        nominalfluss_puent_kg_s = (
            2300.0 / 3600.0
        )  # Nominalfluss bei Zentrale gemaess Auslegung Gadola
        maximalleistung_puent_W = 70000.0  # Maximalleistung Oekofen Puenterswis
        temperaturspreizung_maximalleistung_K = maximalleistung_puent_W / (
            nominalfluss_puent_kg_s * waermekapazitaet_wasser_JkgK
        )
        aussentemperatur_grenze_heizbetrieb_C = 20.0
        aussentemperatur_maximalleistung_C = -14.0
        ruecklauf_bodenheizung_C = 24.0
        reserve_C = 5.0
        temperatur_C = min(
            max(
                self.sensoren.aussentemperatur_Taussen_C,
                aussentemperatur_maximalleistung_C,
            ),
            aussentemperatur_grenze_heizbetrieb_C,
        )
        spreizung_C = (
            (aussentemperatur_grenze_heizbetrieb_C - temperatur_C)
            / (
                aussentemperatur_grenze_heizbetrieb_C
                - aussentemperatur_maximalleistung_C
            )
            * temperaturspreizung_maximalleistung_K
        )
        minimale_temperatur_leistungsueberagung_C = (
            ruecklauf_bodenheizung_C + spreizung_C + reserve_C
        )
        if self.hsm_legionellen.is_state(
            self.hsm_legionellen.state_aktiv
        ) and self.hsm_ladung.is_state(self.hsm_ladung.entry_zwang):
            # print(f'Um die Legionellen zu killen wird eine Fernleitungstemperatur von {self.konstanten.legionellen_fernleitungstemperatur_C:0.2f} gewaehlt')
            return self.konstanten.legionellen_fernleitungstemperatur_C
        fernleitungs_solltemperatur_C = max(
            minimale_temperatur_leistungsueberagung_C,
            self.konstanten.sommer_fernleitung_solltemperatur_warmwasserladung_C,
        )
        # print(f'Um die Anforderung zu erfuellen und die Leistung uebertragen zu koennen wurde eine Fernleitungstemperatur von  {fernleitungs_solltemperatur_C:0.2f} gewaehlt')
        return fernleitungs_solltemperatur_C
