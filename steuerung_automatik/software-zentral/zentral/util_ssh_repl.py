#!/usr/bin/env python
"""
Serve a ptpython console using both telnet and ssh.

Thanks to Vincent Michel for this!
https://gist.github.com/vxgmichel/7685685b3e5ead04ada4a3ba75a48eef
"""

import asyncio
import logging
import pathlib
from typing import List

import asyncssh
from prompt_toolkit import print_formatted_text
from prompt_toolkit.contrib.ssh.server import (
    PromptToolkitSSHServer,
    PromptToolkitSSHSession,
)
from ptpython import repl

from zentral.util_scenarios import ssh_repl_scenarios_history_add


logger = logging.getLogger(__name__)

HISTORY_FEED = ""


async def create(repl_globals: dict, hausnummern: List[int], ssh_port: int = 8022) -> None:
    def read_key(filename: str = "~/.ssh/id_rsa") -> str:
        path = pathlib.Path(filename).expanduser()
        if not path.exists():
            raise Exception(f"{filename}: Does not exist!")
        return str(path)

    def get_history_filename() -> str:
        filename = "~/prompt_toolkit_history.txt"
        path = pathlib.Path(filename).expanduser()
        with path.open("w", encoding="utf-8") as f:
            ssh_repl_scenarios_history_add(f, hausnummern=hausnummern)
        return str(path)

    async def interact(connection: PromptToolkitSSHSession) -> None:
        global_dict = {
            # **globals(),
            **repl_globals,
            "print": print_formatted_text,
            "logger": logger,
        }

        def configure(python_repl: repl.PythonRepl) -> None:
            python_repl.confirm_exit = False

        await repl.embed(
            return_asyncio_coroutine=True,
            configure=configure,
            globals=global_dict,
            history_filename=get_history_filename(),
        )

    ssh_server = PromptToolkitSSHServer(interact=interact, enable_cpr=False)

    def server_factory() -> PromptToolkitSSHServer:
        logger.info("Connection to ssh_repl!")
        return ssh_server

    await asyncssh.create_server(server_factory=server_factory, host="", port=ssh_port, server_host_keys=[read_key()])
    logger.info(f"Access repl using: ssh -p {ssh_port} localhost")


async def main() -> None:
    await create(repl_globals={})
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
