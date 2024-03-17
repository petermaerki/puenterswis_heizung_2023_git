import asyncio

import logging

# https://asyncssh.readthedocs.io/en/latest/
# https://github.com/prompt-toolkit/ptpython/blob/master/examples/asyncio-ssh-python-embed.py
# https://github.com/prompt-toolkit/python-prompt-toolkit/issues/934
# https://github.com/prompt-toolkit/ptpython
# ssh-keygen -f ~/.ssh/id_rsa
import asyncssh
from ptpython.contrib.asyncssh_repl import ReplSSHServerSession

# from zentral import config_bochs

# from zentral.context import Context
# from zentral.context_mock import ContextMock
from zentral.util_logger import initialize_logger


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


# async def interactive_shell() -> None:
#     """
#     Coroutine that starts a Python REPL from which we can access the global
#     counter variable.
#     """
#     print(
#         'You should be able to read and update the "counter[0]" variable from this shell.'
#     )
#     try:
#         await embed(globals=globals(), return_asyncio_coroutine=True, patch_stdout=True)
#     except EOFError:
#         # Stop the loop when quitting the repl. (Ctrl-D press.)
#         loop.stop()


class MySSHServer(asyncssh.SSHServer):
    """
    Server without authentication, running `ReplSSHServerSession`.
    """

    def __init__(self, get_namespace):
        print(f"Connected {get_namespace()}")
        self.get_namespace = get_namespace
        # os.environ["PROMPT_TOOLKIT_NO_CPR"] = "1"

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

        # def session_requested(self):
        # return ReplSSHServerSession(self.get_namespace)


async def main():
    if True:
        port = 8222
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
            server_host_keys=["~/.ssh/id_rsa"],
            # server_host_keys=["/etc/ssh/ssh_host_dsa_key"],
        )
        # await asyncio.Future()  # Wait forever.

    # await interactive_shell()
    await asyncio.Future()  # Wait forever.
    print("Done")


if __name__ == "__main__":
    initialize_logger()

    asyncio.run(main(), debug=True)
