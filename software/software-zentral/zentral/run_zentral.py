import argparse
import asyncio
import logging

from config import raspi_os_config

from zentral import config_etappe
from zentral.context import Context
from zentral.context_mock import ContextMock
from zentral.util_logger import initialize_logger

logger = logging.getLogger(__name__)


async def start_application(ctx: Context) -> None:
    await ctx.init()
    await ctx.create_ssh_repl()

    # The pcbs_dezentral are essential for the following calculations: Initialize it first!
    await ctx.modbus_communication.read_modbus_pcbs_dezentral_heizzentrale()
    try:
        await ctx.modbus_communication.read_modbus_oekofen()
    except Exception as e:
        logger.warning(f"Initial reading of oekofen-modbus failed: {e}")
        logger.exception(e)

    asyncio.create_task(ctx.modbus_communication.task_modbus_haeuser())
    asyncio.create_task(ctx.modbus_communication.task_modbus_oekofen())
    asyncio.create_task(ctx.task_hsm())
    asyncio.create_task(ctx.task_verbrauch())
    asyncio.create_task(ctx.task_mbus())


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mocked", help="increase output verbosity", action="store_true")
    args = parser.parse_args()
    ContextClass = ContextMock if args.mocked else Context

    async with ContextClass(config_etappe.create_config_etappe(hostname=raspi_os_config.hostname)) as ctx:
        await start_application(ctx=ctx)

        await asyncio.Future()  # Wait forever.
        print("Done")


if __name__ == "__main__":
    initialize_logger()

    asyncio.run(main(), debug=False)
