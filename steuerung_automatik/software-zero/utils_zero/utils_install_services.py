from typing import Iterator
from utils_common.utils_install import run
from utils_zero.utils_install import (
    GID_ROOT,
    STAT_RWX_RX_RX,
    UID_ROOT,
    assert_su,
    install_file,
)
from utils_zero.utils_constants import ZEROES
from config import raspi_os_config


def service_stems(zero_name: str = None) -> Iterator[str]:
    yield "heizung-app"
    if zero_name is None:
        for zero_name in ZEROES:
            yield f"heizung-ssh-tunnel_{zero_name}"
        return

    assert zero_name in ZEROES
    yield f"heizung-ssh-tunnel_{zero_name}"


def install_services():
    assert_su()

    for service_stem in service_stems():
        install_file(
            rootfspath=f"/etc/systemd/system/{service_stem}.service",
            uid=UID_ROOT,
            gid=GID_ROOT,
            mode=STAT_RWX_RX_RX,
        )

    for service_stem in service_stems():
        run(["systemctl", "disable", service_stem])

    for service_stem in service_stems(zero_name=raspi_os_config.hostname):
        run(["systemctl", "enable", service_stem])

    for service_stem in service_stems(zero_name=raspi_os_config.hostname):
        run(["systemctl", "restart", service_stem])
