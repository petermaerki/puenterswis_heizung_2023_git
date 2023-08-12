#!/usr/bin/python
#
# .bashrc is not initialized yet!
#
# This is the only script which has to set the path!!
#
# How to run the script:
#    cd /home/zero/puenterswis_heizung_2023_git/steuerung_automatik/zero-software/install
#    sudo python 625_zero-root_bootstrap.py
#
import os
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

    utils_install.ask()

    utils_install.install_hostname()
    utils_install.install_wlan()

    utils_install.create_softlink_zerosoftware()

    utils_install.copy_bashrc()
    utils_install.copy_ssh()

    utils_install_webtunnel.install_web_tunnel()

    input("Reboot now? <ctrl-C>: abort, <ENTER>: reboot")
    os.system("reboot --reboot")


if __name__ == "__main__":
    main()
