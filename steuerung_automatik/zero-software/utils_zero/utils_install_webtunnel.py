from utils_common.utils_install import run
from utils_zero.utils_install import (
    GID_ROOT,
    STAT_RW_R_R,
    UID_ROOT,
    assert_su,
    install_file,
)

SERVICE_STEM = "web-tunnel"
SERVICE_NAME = f"{SERVICE_STEM}.service"


def install_web_tunnel():
    assert_su()

    install_file(
        rootfspath=f"/etc/systemd/system/{SERVICE_NAME}",
        uid=UID_ROOT,
        gid=GID_ROOT,
        mode=STAT_RW_R_R,
    )

    run(["systemctl", "enable", SERVICE_NAME])

    run(["systemctl", "restart", SERVICE_NAME])
