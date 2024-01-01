# scripts/example/simple_rtu_client.py
import sys
import time
import pathlib

import serial
import fcntl
import struct
from typing import List
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
    ports.sort(key=lambda p: p.device)
    if True:
        # Waveshare USB to RS485
        vid = 0x0403  # Vendor Id
        pid = 0x6001  # Product Id
        product = 'FT232R USB UART'
    if False:
        # Waveshare USB to RS485 (B)
        vid = 0x1A86  # Vendor Id
        pid = 0x55D3  # Product Id
        product = "USB Single Serial"
    if False:
        # Waveshare USB to 4Ch RS485
        vid = 0x1A86  # Vendor Id
        pid = 0x55D3  # Product Id
        product = "USB Quad_Serial"

    for port in ports:
        if port.product != product:
            continue
        if port.vid != vid:
            continue
        return port.device

    raise Exception(f"No serial interface found for {vid=} {product=}")


def get_serial_port():
    port = find_serial_port()
    """Return serial.Serial instance, ready to use for RS485."""
    port = serial.Serial(
        port=port,
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=1,
        bytesize=8,
        timeout=0.2,
    )

    if False:
        fh = port.fileno()

        # A struct with configuration for serial port.
        serial_rs485 = struct.pack("hhhhhhhh", 1, 0, 0, 0, 0, 0, 0, 0)
        fcntl.ioctl(fh, 0x542F, serial_rs485)

    return port


class Context:
    def __init__(self, config_baubaschnitt: config_base.ConfigBauetappe):
        self.serial_port = get_serial_port()
        self.config_baubaschnitt = config_baubaschnitt

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.serial_port.close()
        return False

    def modbus_haueser_loop(self) -> None:
        for haus in self.config_baubaschnitt.haeuser:
            self.handle_haus(haus)

            # self.reboot_reset(haus=haus)

    def handle_haus(self, haus: config_base.Haus) -> None:
        iregs_all = portable_modbus_registers.IregsAll()
        message = rtu.read_input_registers(
            slave_id=haus.config_haus.modbus_client_id,
            starting_address=portable_modbus_registers.EnumModbusRegisters.SETGET16BIT_ALL,
            quantity=iregs_all.register_count,
        )

        try:
            response = rtu.send_message(message, self.serial_port)
        except ValueError:
            print("ValueError")
            haus.status_haus.modbus_history.failed()
            return

        assert len(response) == iregs_all.register_count
        haus.status_haus.modbus_success_iregs = response
        haus.status_haus.modbus_history.success()
        print(f"Iregsall: {response}")
        time.sleep(0.006)

    def reboot_reset(self, haus: config_base.Haus):
        message = rtu.write_single_coil(
            slave_id=haus.config_haus.modbus_client_id,
            address=portable_modbus_registers.EnumModbusRegisters.SETGET1BIT_REBOOT_WATCHDOG,
            value=1,
        )
        response = rtu.send_message(message, self.serial_port)
        print("Reboot")



def main():
    with Context(config_bochs.config_bauabschnitt_bochs) as ctx:
        while True:
            print("")
            ctx.modbus_haueser_loop()
            haus = ctx.config_baubaschnitt.haeuser[0].status_haus
            print(haus.modbus_history.text_history)
            time.sleep(1.0)


if __name__ == "__main__":
    main()
