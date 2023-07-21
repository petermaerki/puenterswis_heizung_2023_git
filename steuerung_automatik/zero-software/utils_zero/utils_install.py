import getpass
import os
import pathlib
import stat
import sys

from utils_common.utils_constants import ID_RSA, ID_RSA_PUB
from utils_zero.utils_constants import (
    DIRECTORY_ROOTFS,
    DIRECTORY_SSH,
    DIRECTORY_ZEROSOFTWARE,
    DIRECTORY_ZEROSOFTWARE_LINK,
    FILENAME_BASHRC_ROOT,
    FILENAME_BASHRC_ZERO,
    ZERO_NAME,
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
            f"Please paste 'keys/zero_{ZERO_NAME}/{ID_RSA}' and terminate with <ctrl-d>!"
        )
        lines = sys.stdin.readlines()
        filename_new.write_text("".join(lines))
        os.chown(filename_new, uid=UID_ZERO, gid=GID_ZERO)
        filename_new.chmod(mode=STAT_RW)

    DIRECTORY_KEYS = DIRECTORY_ZEROSOFTWARE / "keys"
    copyssh_file(DIRECTORY_KEYS / "authorized_keys")
    copyssh_file(DIRECTORY_KEYS / ZERO_NAME / ID_RSA_PUB)
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
