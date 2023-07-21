from utils_common.utils_constants import ZEROES_DIR
from utils_pclinux.utils_install_keygen import do_encrypt


def main():
    for zero_dir in ZEROES_DIR:
        do_encrypt(zero_dir=zero_dir)


if __name__ == "__main__":
    main()
