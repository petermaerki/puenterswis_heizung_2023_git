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
    ctx.dispatch(HsmTimeSignal(time_s=5.0))
    ctx.dispatch(HsmTimeSignal(time_s=5.0))
    ctx.sensoren.zentralspeicher_oben_Tszo_C = 30.0
    ctx.dispatch(HsmTimeSignal(time_s=5.0))


if __name__ == "__main__":
    main()
