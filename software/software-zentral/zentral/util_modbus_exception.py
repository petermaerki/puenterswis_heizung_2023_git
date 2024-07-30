from __future__ import annotations

import logging
import os
import typing
from contextlib import asynccontextmanager

if typing.TYPE_CHECKING:
    from context import Context

logger = logging.getLogger(__name__)


@asynccontextmanager
async def exception_handler_and_exit(ctx: Context, task_name: str, exit_code: int):
    """
    If an unexpected exception occours:
      * the exception will be logged
      * cleanup tasks will be executed
      * 'os.exit()' will be called
    """
    assert isinstance(task_name, str)
    assert isinstance(exit_code, int)

    async def cleanup_tasks() -> None:
        await ctx.close_and_flush_influx()

    async def do_exit(e: BaseException, prefix: str) -> typing.NoReturn:
        logger.error(f"{prefix}. Exit code {exit_code}, Task '{task_name}', Unexpected {e!r}")
        logger.exception(e)
        await cleanup_tasks()
        os._exit(exit_code)

    try:
        yield
    except Exception as e:
        await do_exit(e, "Fatal error")
    except SystemExit as e:
        await do_exit(e, "Application wants to terminate")
