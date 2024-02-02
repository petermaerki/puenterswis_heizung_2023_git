# scripts/example/simple_rtu_client.py
import asyncio

# import fcntl
import logging
import os

import asyncssh
import config_bochs

from pymodbus import ModbusException

from src.context import Context
from src.config_base import ConfigBauabschnitt
from src.utils_logger import initialize_logger


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


async def interactive_shell() -> None:
    """
    Coroutine that starts a Python REPL from which we can access the global
    counter variable.
    """
    print(
        'You should be able to read and update the "counter[0]" variable from this shell.'
    )
    try:
        await embed(globals=globals(), return_asyncio_coroutine=True, patch_stdout=True)
    except EOFError:
        # Stop the loop when quitting the repl. (Ctrl-D press.)
        loop.stop()


class MySSHServer(asyncssh.SSHServer):
    """
    Server without authentication, running `ReplSSHServerSession`.
    """

    def __init__(self, get_namespace):
        print(f"Connected {get_namespace()}")
        self.get_namespace = get_namespace
        os.environ["PROMPT_TOOLKIT_NO_CPR"] = "1"

    def begin_auth(self, username):
        # No authentication.
        print("No authentication")
        return False

    def session_requested(self):
        print("session_requested")
        print(f"{ReplSSHServerSession=}")
        session = ReplSSHServerSession(self.get_namespace)
        print(f"{session=}")
        return session


async def main(port: int = 8222):
    if False:
        # Namespace exposed in the REPL.
        environ = {"hello": "world"}

        # Start SSH server.
        def create_server() -> MySSHServer:
            return MySSHServer(lambda: environ)

        print("Listening on :%i" % port)
        print('To connect, do "ssh localhost -p %i"' % port)

        await asyncssh.create_server(
            create_server,
            "",
            port,
            server_host_keys=["/home/maerki/.ssh/id_rsa"],
            # server_host_keys=["/etc/ssh/ssh_host_dsa_key"]
        )
        # await asyncio.Future()  # Wait forever.

    async with Context(config_bochs.config_bauabschnitt_bochs) as ctx:
        await asyncio.create_task(ctx.modbus_communication.task_modbus())

    # await interactive_shell()
    await asyncio.Future()  # Wait forever.
    print("Done")


if __name__ == "__main__":
    initialize_logger()

    asyncio.run(main(), debug=False)
