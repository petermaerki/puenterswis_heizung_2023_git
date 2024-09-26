import os
from contextlib import asynccontextmanager

from config import raspi_os_config
from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse

from zentral import config_etappe
from zentral.context import Context
from zentral.context_mock import ContextMock
from zentral.run_zentral import start_application
from zentral.util_logger import initialize_logger
from zentral.util_scenarios import SCENARIO_CLASSES, SCENARIOS

initialize_logger()


class Globals:
    def __init__(self):
        self.ctx: Context = None


_GLOBALS = Globals()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # https://fastapi.tiangolo.com/advanced/events/
    # http://127.0.0.1:8000/predict?x=2
    #  ==> 84
    mocked = os.environ.get("HEIZUNG2023_MOCKED", "0") != "0"
    cls_ctx = ContextMock if mocked else Context

    async with cls_ctx(config_etappe.create_config_etappe(hostname=raspi_os_config.hostname)) as ctx:
        _GLOBALS.ctx = ctx
        await start_application(ctx=ctx)

        yield

        _GLOBALS.ctx = None


app = FastAPI(lifespan=lifespan)


for cls_scenario in SCENARIO_CLASSES:

    async def f(scenario: cls_scenario = Depends()):
        SCENARIOS.add(ctx=_GLOBALS.ctx, scenario=scenario)
        return {"result": repr(scenario)}

    path = f"/scenario/{cls_scenario.__name__}"
    app.add_api_route(path=path, name=cls_scenario.__name__, endpoint=f, methods=["GET"])


@app.get("/")
async def redirect_root():
    return RedirectResponse("/docs#")
