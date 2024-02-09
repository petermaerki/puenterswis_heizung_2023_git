from enum import Enum
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI


class BackgroundRunner:
    def __init__(self):
        self.value = 0

    async def run_main(self):
        while True:
            await asyncio.sleep(0.1)
            self.value += 1


runner = BackgroundRunner()


def fake_answer_to_everything_ml_model(x: float):
    return x * 42


class EnumEvent(str, Enum):
    tesla = "Tesla"
    volvo = "Volvo"
    fiat = "Fiat"


ml_models = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # https://fastapi.tiangolo.com/advanced/events/
    # http://127.0.0.1:8000/predict?x=2
    #  ==> 84
    asyncio.create_task(runner.run_main())

    # Load the ML model
    ml_models["answer_to_everything"] = fake_answer_to_everything_ml_model
    yield
    # Clean up the ML models and release the resources
    ml_models.clear()


app = FastAPI(lifespan=lifespan)


@app.get("/predict")
async def predict(x: float):
    result = ml_models["answer_to_everything"](x)
    return {"result": result}


@app.get("/mock/haus")
async def mock_hans(i: int, car_type: EnumEvent):
    # https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
    result = str(i)
    return {"result": result}
