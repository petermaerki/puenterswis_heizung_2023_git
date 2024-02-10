import getpass
import importlib
import os
import pathlib
import re
import shutil
import stat
import sys
import textwrap

from config import raspi_os_config
from utils_common.utils_constants import ID_RSA, ID_RSA_ASC, ID_RSA_PUB
from utils_common.utils_install import run
from utils_zero.utils_constants import (
    DIRECTORY_ROOTFS,
    DIRECTORY_SSH,
    DIRECTORY_ZEROSOFTWARE,
    DIRECTORY_ZEROSOFTWARE_LINK,
    FILENAME_BASHRC_ROOT,
    FILENAME_BASHRC_ZERO,
    FILENAME_CONFIG,
    ZEROES,
)

UID_ROOT = 0
GID_ROOT = 0
UID_ZERO = 1000
GID_ZERO = 1000

STAT_RW = stat.S_IRUSR | stat.S_IWUSR
STAT_RW_R_R = STAT_RW | stat.S_IRGRP | stat.S_IROTH
STAT_RW_RW_R = STAT_RW_R_R | stat.S_IWGRP


def assert_su():
    user = getpass.getuser()
    expected_user = "root"
    assert user == expected_user, f"Expected to be '{expected_user}' and not '{user}'!"


def ask():
    print(f"Ask for configuration and store in: {FILENAME_CONFIG}")

    if FILENAME_CONFIG.exists():
        print("Existing configuration: ")
        print(textwrap.indent(text=FILENAME_CONFIG.read_text().strip(), prefix="    "))
        print("")

    def input_default(prompt: str, default: str) -> str:
        user_input = input(f"{prompt} <ENTER> for '{default}': ")
        if len(user_input) == 0:
            return default
        return user_input

    hostname = input_default(
        f"Hostname ({','.join(ZEROES)}): ", raspi_os_config.hostname
    )
    assert hostname in ZEROES
    wlan_ssid = input_default("WLAN ssid: ", raspi_os_config.wlan_ssid)
    wlan_pw = input_default("WLAN pw: ", raspi_os_config.wlan_pw)

    FILENAME_CONFIG.write_text(
        f"""
hostname = "{hostname}"
wlan_ssid = "{wlan_ssid}"
wlan_pw = "{wlan_pw}"
"""
    )

    importlib.reload(raspi_os_config)


def install_hostname() -> None:
    run(
        [
            "raspi-config",
            "nonint",
            "do_hostname",
            raspi_os_config.hostname,
        ]
    )
    if False:
        filename_hostname = pathlib.Path("/etc/hostname")
        filename_hostname.write_text(raspi_os_config.hostname + "\n")

        filename_hosts = pathlib.Path("/etc/hosts")
        hosts = filename_hosts.read_text()
        hosts = re.sub("(zero-\w+)", hosts, raspi_os_config.hostname)
        filename_hosts.write_text(hosts)


def install_wlan() -> None:
    run(
        [
            "raspi-config",
            "nonint",
            "do_wifi_country",
            "CH",
        ]
    )

    hidden = "0"
    plain = "1"
    run(
        [
            "raspi-config",
            "nonint",
            "do_wifi_ssid_passphrase",
            raspi_os_config.wlan_ssid,
            raspi_os_config.wlan_pw,
            hidden,
            plain,
        ]
    )

    if False:
        filename_wpa_supplicant = pathlib.Path(
            "/etc/wpa_supplicant/wpa_supplicant.conf"
        )
        wpa_supplicant = f"""
    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1
    country=CH

    network={{
            ssid="{raspi_os_config.wlan_ssid}"
            psk="{raspi_os_config.wlan_pw}"
    }}
    """
        filename_wpa_supplicant.write_text(wpa_supplicant)


def install_file(
    rootfspath: str, mode: str = None, uid: str = None, gid: str = None
) -> None:
    assert isinstance(rootfspath, str)
    assert rootfspath.startswith("/")
    payload = (DIRECTORY_ROOTFS / rootfspath[1:]).read_text()
    filename_out = pathlib.Path(rootfspath)
    filename_out.parent.mkdir(parents=True, exist_ok=True)
    filename_out.write_text(payload)

    if uid is not None:
        assert isinstance(uid, int)
        assert isinstance(gid, int)
        os.chown(path=filename_out, uid=uid, gid=gid)

    if mode is not None:
        assert isinstance(mode, int)
        filename_out.chmod(mode=mode)


def copy_ssh() -> None:
    def copyssh_file(filename: pathlib.Path) -> None:
        text = filename.read_text()
        filename_new = DIRECTORY_SSH / filename.name
        filename_new.write_text(text)
        os.chown(filename_new, uid=UID_ZERO, gid=GID_ZERO)
        filename_new.chmod(mode=STAT_RW_R_R)

    def copyssh_ask_user() -> None:
        filename_new = DIRECTORY_SSH / ID_RSA
        if filename_new.exists():
            print(f"{filename_new}: exists: Skip asking for content!")
            return
        print(
            f"Please paste 'keys/{raspi_os_config.hostname}/{ID_RSA_ASC}' and terminate with <ctrl-d>!"
        )
        lines = sys.stdin.readlines()
        filename_new.write_text("".join(lines))
        os.chown(filename_new, uid=UID_ZERO, gid=GID_ZERO)
        filename_new.chmod(mode=STAT_RW)

    DIRECTORY_SSH.mkdir(exist_ok=True)
    shutil.chown(DIRECTORY_SSH, "zero", "zero")

    DIRECTORY_KEYS = DIRECTORY_ZEROSOFTWARE / "keys"
    copyssh_file(DIRECTORY_KEYS / "authorized_keys")
    copyssh_file(DIRECTORY_KEYS / raspi_os_config.hostname / ID_RSA_PUB)
    copyssh_ask_user()


def copy_bashrc() -> None:
    install_file(
        rootfspath=str(FILENAME_BASHRC_ROOT),
        uid=UID_ROOT,
        gid=GID_ROOT,
        mode=STAT_RW_R_R,
    )
    install_file(
        rootfspath=str(FILENAME_BASHRC_ZERO),
        uid=UID_ZERO,
        gid=GID_ZERO,
        mode=STAT_RW_R_R,
    )


def create_softlink_zerosoftware():
    DIRECTORY_ZEROSOFTWARE_LINK.unlink(missing_ok=True)
    DIRECTORY_ZEROSOFTWARE_LINK.symlink_to(
        DIRECTORY_ZEROSOFTWARE, target_is_directory=True
    )
    os.chown(
        DIRECTORY_ZEROSOFTWARE_LINK, uid=UID_ZERO, gid=GID_ZERO, follow_symlinks=False
    )
