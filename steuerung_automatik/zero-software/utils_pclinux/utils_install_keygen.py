import pathlib

from utils_common.utils_constants import ID_RSA, ID_RSA_ASC, ID_RSA_PUB
from utils_common.utils_install import run


def do_encrypt(zero_dir: pathlib.Path):
    run(
        [
            "gpg",
            "--encrypt",
            "--yes",
            "--armour",
            "--output",
            str(zero_dir / ID_RSA_ASC),
            "--recipient",
            "hans@maerki.com",
            "--recipient",
            "peter@maerki.com",
            str(zero_dir / ID_RSA),
        ]
    )


def do_decrypt(zero_dir: pathlib.Path):
    run(
        [
            "gpg",
            "--decrypt",
            "--yes",
            "--output",
            str(zero_dir / ID_RSA),
            str(zero_dir / ID_RSA_ASC),
        ]
    )


def do_ssh_keygen(zero_dir: pathlib.Path):
    for file in (
        ID_RSA,
        ID_RSA_ASC,
        ID_RSA_PUB,
    ):
        (zero_dir / file).unlink(missing_ok=True)

    run(
        [
            "ssh-keygen",
            "-f",
            str(zero_dir / ID_RSA),
            "-C",
            zero_dir.name,
            "-N",
            "",
            "-t",
            "rsa",
            "-b",
            "4096",
        ]
    )
