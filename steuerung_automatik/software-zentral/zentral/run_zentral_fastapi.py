from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import Depends, FastAPI
import uvicorn

from zentral.util_scenarios import SCENARIO_CLASSES, SCENARIOS
from zentral.context_mock import ContextMock
from zentral import config_bochs


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


class Globals:
    def __init__(self):
        self.ctx: ContextMock = None


globals = Globals()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # https://fastapi.tiangolo.com/advanced/events/
    # http://127.0.0.1:8000/predict?x=2
    #  ==> 84
    async with ContextMock(config_bochs.config_bauabschnitt_bochs) as ctx:
        asyncio.create_task(ctx.modbus_communication.task_modbus())

        # Load the ML model
        globals.ctx = ctx
        yield


app = FastAPI(lifespan=lifespan)


for cls_scenario in SCENARIO_CLASSES:

    async def f(scenario: cls_scenario = Depends()):
        SCENARIOS.add(scenario)
        return {"result": repr(scenario)}

    # app.route(f,path= f"/scenario/{s.__class__.__name__}", methods=["GET"])

    path = f"/scenario/{cls_scenario.__name__}"
    app.add_api_route(
        path=path, name=cls_scenario.__name__, endpoint=f, methods=["GET"]
    )


if __name__ == "__main__":
    uvicorn.run("run_zentral_fastapi:app", reload=True)
