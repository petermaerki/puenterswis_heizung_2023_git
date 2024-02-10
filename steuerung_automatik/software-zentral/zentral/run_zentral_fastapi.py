from contextlib import asynccontextmanager
import asyncio
import os

from fastapi import Depends, FastAPI

from zentral import config_bochs
from zentral.util_scenarios import SCENARIO_CLASSES, SCENARIOS
from zentral.context_mock import Context, ContextMock
from zentral.utils_logger import initialize_logger


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

    async with cls_ctx(config_bochs.create_config_bochs()) as ctx:
        globals.ctx = ctx

        asyncio.create_task(ctx.modbus_communication.task_modbus())
        yield


app = FastAPI(lifespan=lifespan)

# if True:
#     config_etappe = config_bochs.create_config_bochs()
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
