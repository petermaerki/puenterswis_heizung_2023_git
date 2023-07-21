import pathlib
import socket

from utils_common.utils_constants import DIRECTORY_WORKSPACE, ZEROES

# top directories
DIRECTORY_ROOTFS = DIRECTORY_WORKSPACE / "rootfs"
DIRECTORY_HOME_ZERO = pathlib.Path("/home/zero")
DIRECTORY_HOME_ROOT = pathlib.Path("/root")

# SSH
DIRECTORY_SSH = DIRECTORY_HOME_ZERO / ".ssh"
DIRECTORY_SSH.mkdir(exist_ok=True)

# BASHRC
FILENAME_BASHRC_ZERO = DIRECTORY_HOME_ZERO / ".bashrc"
FILENAME_BASHRC_ROOT = DIRECTORY_HOME_ROOT / ".bashrc"

# zero-software
DIRECTORY_ZEROSOFTWARE = (
    DIRECTORY_HOME_ZERO
    / "puenterswis_heizung_2023_git/steuerung_automatik/zero-software"
)
DIRECTORY_ZEROSOFTWARE_LINK = DIRECTORY_HOME_ZERO / "zero-software"

ZERO_NAME = socket.gethostname()
assert ZERO_NAME in ZEROES
