import pathlib

from program.context import Context
from program.hsm_signal import HsmTimeSignal
from program.utils_logger import initialize_logger

DIRECTORY_THIS_FILE = pathlib.Path(__file__).parent


def main():
    initialize_logger()
    ctx = Context()
    ctx.sensoren.zentralspeicher_oben_Tszo_C = 80.0
    ctx.sensoren.anforderung = True
    # ctx.hsm_ladung.force_state(ctx.hsm_ladung.state_bedarf)
    time_s = 5.0
    ctx.dispatch(HsmTimeSignal(time_s=time_s))
    time_s += 6*60.0
    ctx.dispatch(HsmTimeSignal(time_s=time_s))
    ctx.sensoren.zentralspeicher_oben_Tszo_C = 30.0
    time_s += 2*60.0
    ctx.dispatch(HsmTimeSignal(time_s=time_s))
    for temp in range(-20, 30, 5):
        ctx.sensoren.aussentemperatur_Taussen_C = temp
        print (temp, ctx.fernleitungs_solltemperatur_C)


if __name__ == "__main__":
    main()
