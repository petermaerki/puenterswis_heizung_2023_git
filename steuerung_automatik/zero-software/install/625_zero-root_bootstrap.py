#!/usr/bin/python
#
# .bashrc is not initialized yet!
#
# This is the only script which has to set the path!!
#
import pathlib
import sys

DIRECTORY_ZEROSOFTWARE = pathlib.Path(
    "/home/zero/puenterswis_heizung_2023_git/steuerung_automatik/zero-software"
)
assert DIRECTORY_ZEROSOFTWARE.exists()

# Add path to allow access to uitls
sys.path.insert(0, str(DIRECTORY_ZEROSOFTWARE))
from utils_zero import utils_install, utils_install_webtunnel  # noqa: E402


def main():
    utils_install.assert_su()

    utils_install.create_softlink_zerosoftware()

    utils_install.copy_bashrc()
    utils_install.copy_ssh()

    utils_install_webtunnel.install_web_tunnel()


if __name__ == "__main__":
    main()
