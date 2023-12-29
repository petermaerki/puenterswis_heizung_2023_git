# scripts/example/simple_rtu_client.py
import sys
import time
import pathlib

import serial
from serial.tools import list_ports
from umodbus.client.serial import rtu

import config_base
import config_bochs

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent.absolute()
DIRECTORY_MICROPYTHON = (
    DIRECTORY_OF_THIS_FILE.parent.parent / "software-dezentral" / "micropython"
)
assert DIRECTORY_MICROPYTHON.is_dir()
sys.path.append(str(DIRECTORY_MICROPYTHON))

import portable_modbus_registers

modbus_time_1char_ms = 11 / 9600


def find_serial_port() -> str:
    ports = list(list_ports.comports())

    vid = 0x1A86
    pid = 0x55D3
    product = "USB Single Serial"
    for port in ports:
        if port.product != product:
            continue
        if port.vid != vid:
            continue
        return port.device


def get_serial_port():
    port = find_serial_port()
    """Return serial.Serial instance, ready to use for RS485."""
    port = serial.Serial(
        port=port,
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=1,
        bytesize=8,
        timeout=0.1,
    )

    fh = port.fileno()

    # A struct with configuration for serial port.
    # serial_rs485 = struct.pack("hhhhhhhh", 1, 0, 0, 0, 0, 0, 0, 0)
    # fcntl.ioctl(fh, 0x542F, serial_rs485)

    return port


class Context:
    def __init__(self, config_baubaschnitt: config_base.ConfigBauabschnitt):
        self.serial_port = get_serial_port()
        self.config_baubaschnitt = config_baubaschnitt

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.serial_port.close()
        return False

    def modbus_haueser_loop(self) -> None:
        for haus in self.config_baubaschnitt.haeuser:
            self.handle_hans(haus)

    def handle_hans(self, haus: config_base.Haus) -> None:
        iregs_all = portable_modbus_registers.IregsAll()
        message = rtu.read_input_registers(
            slave_id=haus.config_haus.modbus_client_id,
            starting_address=portable_modbus_registers.EnumModbusRegisters.IREGS_ALL,
            quantity=iregs_all.register_count,
        )

        try:
            response = rtu.send_message(message, self.serial_port)
        except ValueError:
            print("ValueError")
            haus.status_haus.modbus_failed_s.add()
            return

        assert len(response) == iregs_all.register_count
        haus.status_haus.modbus_success_iregs = response
        haus.status_haus.modbus_success_s.add()
        print(f"Iregsall: {response}")
        time.sleep(0.006)


def main():
    with Context(config_bochs.config_bauabschnitt_bochs) as ctx:
        while True:
            ctx.modbus_haueser_loop()
            haus = ctx.config_baubaschnitt.haeuser[0].status_haus
            print("")
            print(f"{haus.modbus_failed_s.timestamps_s}")
            print(f"{haus.modbus_success_s.timestamps_s}")
            print(f"{haus.modbus_ok}")
            time.sleep(1.0)


if __name__ == "__main__":
    main()
