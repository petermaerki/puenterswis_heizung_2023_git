import pathlib

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent.absolute()

DIRECTORY_WORKSPACE = DIRECTORY_OF_THIS_FILE.parent
assert (DIRECTORY_WORKSPACE / "software-zero.code-workspace").exists()

# top directories
DIRECTORY_KEYS = DIRECTORY_WORKSPACE / "keys"

# ssh
ID_RSA = "id_rsa"
ID_RSA_ASC = "id_rsa.asc"
ID_RSA_PUB = "id_rsa.pub"

# Zeroes
ZEROES = ("zero-virgin", "zero-puent", "zero-bochs")
ZEROES_DIR = (pathlib.Path(DIRECTORY_KEYS / zero_name) for zero_name in ZEROES)

DICT_SSH_TUNNEL_PORT = {
    "zero-virgin": 8851,
    "zero-bochs": 8852,
    "zero-puent": 8853,
}
