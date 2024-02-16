import asyncio
import argparse

import logging

from zentral import config_bochs

from zentral.context import Context
from zentral.context_mock import ContextMock
from zentral.utils_logger import initialize_logger


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mocked", help="increase output verbosity", action="store_true")
    args = parser.parse_args()
    ContextClass = ContextMock if args.mocked else Context

    async with ContextClass(config_bochs.create_config_bochs()) as ctx:
        await asyncio.create_task(ctx.modbus_communication.task_modbus())

    # await interactive_shell()
    await asyncio.Future()  # Wait forever.
    print("Done")


if __name__ == "__main__":
    initialize_logger()

    asyncio.run(main(), debug=False)
