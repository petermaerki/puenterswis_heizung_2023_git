import asyncio
import os
from contextlib import asynccontextmanager

from config import raspi_os_config
from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse

from zentral import config_etappe
from zentral.context_mock import Context, ContextMock
from zentral.util_logger import initialize_logger
from zentral.util_scenarios import SCENARIO_CLASSES, SCENARIOS

initialize_logger()


class Globals:
    def __init__(self):
        self.ctx: Context = None


globals = Globals()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # https://fastapi.tiangolo.com/advanced/events/
    # http://127.0.0.1:8000/predict?x=2
    #  ==> 84
    mocked = os.environ.get("HEIZUNG2023_MOCKED", "0") != "0"
    cls_ctx = ContextMock if mocked else Context

    async with cls_ctx(config_etappe.create_config_etappe(hostname=raspi_os_config.hostname)) as ctx:
        await ctx.init()
        await ctx.create_ssh_repl()

        globals.ctx = ctx

        asyncio.create_task(ctx.modbus_communication.task_modbus())
        asyncio.create_task(ctx.task_hsm())
        asyncio.create_task(ctx.task_verbrauch())
        yield


app = FastAPI(lifespan=lifespan)

# if True:
#     config_etappe = config_etappe.create_config_etappe()
#     type_haus_enum = config_etappe.haus_enum
#     for cls_scenario in SCENARIO_CLASSES:
#         if "haus_nummer" in cls_scenario.__annotations__:
#             cls_scenario.__annotations__["haus_nummer"] = type_haus_enum
#         annotation_haus_nummer = cls_scenario.__annotations__.get("haus_nummer", None)
#         field_haus_nummer = cls_scenario.__dataclass_fields__.get("haus_nummer", None)
#         field_haus_nummer.type = type_haus_enum
#         # if hasattr(cls_scenario, "haus_nummer"):
#         #     cls_scenario.haus_nummer = ctx.config_etappe.haus_enum
#         print("Hallo")

for cls_scenario in SCENARIO_CLASSES:

    async def f(scenario: cls_scenario = Depends()):
        SCENARIOS.add(scenario)
        return {"result": repr(scenario)}

    path = f"/scenario/{cls_scenario.__name__}"
    app.add_api_route(path=path, name=cls_scenario.__name__, endpoint=f, methods=["GET"])


@app.get("/")
async def redirect_root():
    return RedirectResponse("/docs#")


# def main():
#     this_file = pathlib.Path(__file__).relative_to(DIRECTORY_ZENTRAL)
#     this_module = str(this_file.parent / this_file.stem).replace("/", ".")
#     reload_dirs = [str(DIRECTORY_REPO)]
#     uvicorn.run(
#         app=f"{this_module}:app",
#         reload=True,
#         reload_dirs=reload_dirs,
#         workers=1,
#     )


# if __name__ == "__main__":
#     main()
