import asyncio
import argparse

import logging

from config import raspi_os_config
from zentral import config_etappe
from zentral.context import Context
from zentral.context_mock import ContextMock
from zentral.util_logger import initialize_logger


logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mocked", help="increase output verbosity", action="store_true")
    args = parser.parse_args()
    ContextClass = ContextMock if args.mocked else Context

    async with ContextClass(config_etappe.create_config_etappe(hostname=raspi_os_config.hostname)) as ctx:
        await ctx.init()

        asyncio.create_task(ctx.modbus_communication.task_modbus())
        asyncio.create_task(ctx.task_hsm())

        # await interactive_shell()
        await asyncio.Future()  # Wait forever.
        print("Done")


if __name__ == "__main__":
    initialize_logger()

    asyncio.run(main(), debug=False)
else:
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
