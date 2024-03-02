from utils_common.utils_install import run
from utils_zero.utils_install import (
    GID_ROOT,
    STAT_RWX_RX_RX,
    UID_ROOT,
    assert_su,
    install_file,
)

SERVICE_STEMS = (
    "heizung-ssh-tunnel",
    "heizung-app.service",
)


def install_services():
    assert_su()

    for service_stem in SERVICE_STEMS:
        service_name = f"{service_stem}.service"
        install_file(
            rootfspath=f"/etc/systemd/system/{service_name}.service",
            uid=UID_ROOT,
            gid=GID_ROOT,
            mode=STAT_RWX_RX_RX,
        )

    run(["systemctl", "enable", service_name])

    run(["systemctl", "restart", service_name])
