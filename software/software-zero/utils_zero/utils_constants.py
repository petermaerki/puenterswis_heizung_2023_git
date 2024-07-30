import pathlib
import socket

from utils_common.utils_constants import DIRECTORY_WORKSPACE, ZEROES

# top directories
DIRECTORY_ROOTFS = DIRECTORY_WORKSPACE / "rootfs"
DIRECTORY_HOME_ZERO = pathlib.Path("/home/zero")
DIRECTORY_HOME_ROOT = pathlib.Path("/root")

# SSH
DIRECTORY_SSH = DIRECTORY_HOME_ZERO / ".ssh"

# BASHRC
FILENAME_BASHRC_ZERO = DIRECTORY_HOME_ZERO / ".bashrc"
FILENAME_BASHRC_ROOT = DIRECTORY_HOME_ROOT / ".bashrc"

# software-zero
DIRECTORY_SOFTWARE_ZERO = DIRECTORY_HOME_ZERO / "puenterswis_heizung_2023_git/steuerung_automatik/software-zero"
DIRECTORY_SOFTWARE_ZERO_LINK = DIRECTORY_HOME_ZERO / "software-zero"
DIRECTORY_SOFTWARE_ZENTRAL = DIRECTORY_HOME_ZERO / "puenterswis_heizung_2023_git/steuerung_automatik/software-zentral"

ZERO_NAME = socket.gethostname()
assert ZERO_NAME in ZEROES

DIRECTORY_CONFIG = DIRECTORY_SOFTWARE_ZERO / "config"
FILENAME_CONFIG = DIRECTORY_CONFIG / "raspi_os_config.py"
assert FILENAME_CONFIG.exists()
