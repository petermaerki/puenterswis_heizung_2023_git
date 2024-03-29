from utils_common.utils_install import run
from utils_common.utils_constants import DICT_SSH_TUNNEL_PORT
from utils_zero.utils_install import (
    GID_ROOT,
    STAT_RWX_RX_RX,
    UID_ROOT,
    assert_su,
    install_file,
)
from utils_zero.utils_constants import DIRECTORY_ROOTFS
from config import raspi_os_config


def _patch_ssh_tunnel_service(filename: str) -> None:
    port = DICT_SSH_TUNNEL_PORT[raspi_os_config.hostname]

    directory_system = DIRECTORY_ROOTFS / "etc/systemd/system"
    text = (directory_system / f"{filename}-template").read_text()
    text = text.replace("<PORT>", str(port))
    (directory_system / filename).write_text(text)


def install_services():
    assert_su()

    _patch_ssh_tunnel_service(
        filename="heizung-ssh-tunnel.service",
    )

    service_stems = ("heizung-app", "heizung-ssh-tunnel")

    for service_stem in service_stems:
        install_file(
            rootfspath=f"/etc/systemd/system/{service_stem}.service",
            uid=UID_ROOT,
            gid=GID_ROOT,
            mode=STAT_RWX_RX_RX,
        )

    for service_stem in service_stems:
        run(["systemctl", "enable", service_stem])

    for service_stem in service_stems:
        run(["systemctl", "restart", service_stem])
