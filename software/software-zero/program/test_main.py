import logging
import pathlib

from program.context import Context
from program.hsm_signal import TimeSignal
from program.util_logger import initialize_logger

DIRECTORY_THIS_FILE = pathlib.Path(__file__).parent

logger = logging.getLogger(__name__)


def main():
    initialize_logger()
    ctx = Context()
    ctx.sensoren.energie_gestern_kWh = 100.0
    ctx.sensoren.zentralspeicher_oben_Tsz4_C = 80.0
    ctx.sensoren.anforderung = False
    ctx.time_s = 0.0
    ctx.dispatch(TimeSignal())
    logger.info("Neu eine Anforderung")
    ctx.sensoren.anforderung = True
    ctx.time_s += 5.0
    ctx.dispatch(TimeSignal())
    logger.info("Anforderung wieder weg")
    ctx.sensoren.anforderung = False
    ctx.time_s += 5.0
    ctx.dispatch(TimeSignal())
    logger.info("Neu eine Anforderung")
    ctx.sensoren.anforderung = True
    ctx.time_s += 5.0
    ctx.dispatch(TimeSignal())
    ctx.sensoren.zentralspeicher_oben_Tsz4_C = 50.0
    logger.info("Zentralspeicher zu kalt")
    ctx.time_s += 5.0
    ctx.dispatch(TimeSignal())
    ctx.sensoren.zentralspeicher_oben_Tsz4_C = 70.0
    logger.info("Zentralspeicher wieder warm")
    ctx.time_s += 5.0
    ctx.dispatch(TimeSignal())
    # ctx.sensoren.brenner_1_on = True
    ctx.sensoren.energie_gestern_kWh = 10.0
    logger.info("Weil gestern kleiner Energieverbrauch wechsel zu status sommer")
    ctx.dispatch(TimeSignal())
    # time_s += 5.0
    # ctx.dispatch(TimeSignal())
    # ctx.hsm_ladung.force_state(ctx.hsm_ladung.state_bedarf)
    # time_s = 5.0
    # ctx.dispatch(TimeSignal())
    # time_s += 6*60.0
    # ctx.dispatch(TimeSignal())
    # ctx.sensoren.zentralspeicher_oben_Tsz4_C = 30.0
    # time_s += 2*60.0
    # ctx.dispatch(TimeSignal())
    # for temp in range(-20, 30, 5):
    #     ctx.sensoren.aussentemperatur_Taussen_C = temp
    #     print (temp, ctx.fernleitungs_solltemperatur_C)


if __name__ == "__main__":
    main()
