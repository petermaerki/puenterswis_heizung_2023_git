from serial import PARITY_NONE, Serial

from zentral.util_modbus import get_serial_port2

modbus_time_1char_ms = 11 / 9600


def get_serial_port():
    """Return serial.Serial instance, ready to use for RS485."""
    port = get_serial_port2()

    serial = Serial(
        port=port,
        baudrate=9600,
        parity=PARITY_NONE,
        stopbits=1,
        bytesize=8,
        timeout=0.1,
    )

    # fh = serial.fileno()

    # A struct with configuration for serial port.
    # serial_rs485 = struct.pack("hhhhhhhh", 1, 0, 0, 0, 0, 0, 0, 0)
    # fcntl.ioctl(fh, 0x542F, serial_rs485)

    return serial
