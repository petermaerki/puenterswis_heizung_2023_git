#!/usr/bin/env python
# scripts/example/simple_rtu_client.py
import fcntl
import struct
import time

from serial import PARITY_NONE, Serial
from umodbus.client.serial import rtu


class EnumModbusRegisters:
    IREGS_VERSION = 40
    IREGS_UPTIME_S = 41
    COILS_RELAIS = 42
    IREGS_TEMP_cK = 50  # 50..57


modbus_time_1char_ms = 11 / 9600


def get_serial_port():
    """Return serial.Serial instance, ready to use for RS485."""
    port = Serial(
        port="/dev/ttyACM1",
        baudrate=9600,
        parity=PARITY_NONE,
        stopbits=1,
        bytesize=8,
        timeout=0.1,
    )

    fh = port.fileno()

    # A struct with configuration for serial port.
    # serial_rs485 = struct.pack("hhhhhhhh", 1, 0, 0, 0, 0, 0, 0, 0)
    # fcntl.ioctl(fh, 0x542F, serial_rs485)

    return port


serial_port = get_serial_port()


def relais():
    # Returns a message or Application Data Unit (ADU) specific for doing
    # Modbus RTU.
    # message = rtu.write_multiple_coils(slave_id=1, starting_address=1, values=[1, 0, 1, 1])
    for coils in ([1, 0, 0, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0, 0, 1]):
        message = rtu.write_multiple_coils(slave_id=1, starting_address=0, values=coils)
        response = rtu.send_message(message, serial_port)
        print(response)

        message = rtu.read_coils(slave_id=1, starting_address=0, quantity=8)

        # Response depends on Modbus function code. This particular returns the
        # amount of coils written, in this case it is.
        response = rtu.send_message(message, serial_port)
        print(response)


def dezentral(slave_id: int):
    # Returns a message or Application Data Unit (ADU) specific for doing
    # Modbus RTU.
    if False:
        message = rtu.read_coils(slave_id=slave_id, starting_address=42, quantity=1)

        response = rtu.send_message(message, serial_port)
        print(response)
    if False:
        # Dummy register
        message = rtu.read_input_registers(
            slave_id=slave_id, starting_address=10, quantity=1
        )

        response = rtu.send_message(message, serial_port)
        print(response)
    if False:
        for value in (0, 1):
            # Relais coil
            message = rtu.write_single_coil(
                slave_id=slave_id, address=EnumModbusRegisters.COILS_RELAIS, value=value
            )

            response = rtu.send_message(message, serial_port)
            print(response)
            time.sleep(1.0)

    if False:
        message = rtu.read_input_registers(
            slave_id=slave_id,
            starting_address=EnumModbusRegisters.IREGS_UPTIME_S,
            quantity=1,
        )

        response = rtu.send_message(message, serial_port)
        print(f"UPTIME_S: {response}")
        time.sleep(0.1)

    if False:
        message = rtu.read_input_registers(
            slave_id=slave_id,
            starting_address=EnumModbusRegisters.IREGS_TEMP_cK,
            quantity=8,
        )

        response = rtu.send_message(message, serial_port)
        print(f"Temp cK: {response}")
        time.sleep(0.1)

    if True:
        message = rtu.read_input_registers(
            slave_id=slave_id,
            starting_address=EnumModbusRegisters.IREGS_VERSION,
            quantity=1,
        )
        # message = rtu.write_multiple_coils(
        #     slave_id=slave_id,
        #     starting_address=EnumModbusRegisters.IREGS_VERSION,
        #     values=(True,)*100,
        # )

        response = rtu.send_message(message, serial_port)
        print(f"Version: {response}")
        time.sleep(0.006)
        # time.sleep(0.1)


start_s = time.time()
errors = 0
for i in range(1000_000):
    try:
        # relais()
        # time.sleep(0.5)
        dezentral(slave_id=64)
        # time.sleep(0.5)
    except ValueError as exc:
        errors+=1
        print("Failed")
        # raise exc
        time.sleep(0.006)
        # break
    if i%100 == 99:
        duration_s = time.time()-start_s
        print(f"********  {i=}, {i/errors:0.0f}calls per error, {1000*duration_s/i:0.0f}ms per call.")
        pass

serial_port.close()
