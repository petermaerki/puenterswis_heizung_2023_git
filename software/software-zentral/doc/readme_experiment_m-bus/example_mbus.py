import asyncio
import contextlib
import time

import meterbus
import serial

address = 254
address = 75
address = 0x829690102D2C400D

secondary_address = "829690102D2C400D"
secondary_address = "830036752D2C400D"

# See Multical 303, table 11.2.3.1
# X20-00-101: Standard Profile Yearly Target data
data_sequence = (
    (1, 60, "Heat energy E1"),
    (2, 63, "Cooling energy E3"),
    (3, 68, "Volume V1"),
    (4, 97, "Energy E8"),
    (5, 110, "Energy E9"),
    (6, 1004, "Operating hours"),
    (7, 175, "Error hour counter"),
    (8, 86, "t1 actual (2 decimals)"),
    (9, 87, "t2 actual (2 decimals)"),
    (10, 89, "t1-t2 diff. temp. (2 decimals)"),
    (11, 80, "Power E1/E3 actual"),
    (12, 143, "Power Max month"),
    (13, 74, "Flow V1 actual"),
    (14, 139, "Flow V1 max month"),
    (15, 369, "Info bits"),
    (16, 348, "Date and Time"),
    (17, 60, "Heat energy E1"),
    (18, 63, "Cooling energy E3"),
    (19, 63, "Cooling energy E3"),
    (20, 68, "Volume V1"),
    (21, 97, "Energy E8"),
    (22, 110, "Energy E9"),
    # (23,128,'Power Max year'),
    # (24,124,'Flow V1 max year'),
    # (25,238,'Date and Time (logged)'),
)


@contextlib.contextmanager
def duration(tag: str):
    begin_s = time.monotonic()
    yield
    print(f"{tag}: {time.monotonic() - begin_s:0.2f}s")


async def main():
    # https://m-bus.com/documentation-wired/05-data-link-layer
    # Since quiescence on the line corresponds to
    # a 1 (Mark), the start bit must be a Space, and the
    # stop bit a Mark. In between the
    # eight data bits and the
    # even parity bit are transmitted, ensuring that at least every eleventh bit is a Mark.
    with serial.Serial(port="/dev/ttyACM2", baudrate=2400, bytesize=8, parity="E", stopbits=1, timeout=0.4) as ser:
        meterbus.debug(False)

        begin_s = time.monotonic()
        meterbus.send_select_frame(ser, secondary_address)
        await asyncio.sleep(0.08)
        with duration("A"):
            data = meterbus.recv_frame(ser, 1)
        frame = meterbus.load(data=data)

        await asyncio.sleep(0.2)
        meterbus.send_request_frame(ser, meterbus.ADDRESS_NETWORK_LAYER)
        await asyncio.sleep(0.7)

        with duration("B"):
            data = meterbus.recv_frame(ser)
        assert isinstance(frame, meterbus.TelegramACK)
        frame = meterbus.load(data=data)
        assert isinstance(frame, meterbus.TelegramLong)
        print(f"Duration Z: {time.monotonic()-        begin_s:0.2f}s")
        print(type(frame))
        print(frame.to_JSON())
        records = frame.interpreted["body"]["records"]
        assert len(records) == 23  # Why not 25?
        # for no1, name in ((1, 'Heat energy E1'),
        #                   (2, 'Cooling energy E3'),
        #                   (6, 'Operating hours'),
        #                   (7, 'Error hour counter'),
        #                   (8, 't1 actual'),
        #                   (9, 't2 actual'),
        #                   (10, 't1-t2 differential temp'),
        #                   (1, 'Heat energy E1'),
        #                   (1, 'Heat energy E1')

        if True:
            for no1, register_id, register_name in data_sequence:
                print(f"*** {register_name}: {records[no1-1]}")
        print("....")
        # for record in frame.records:
        #     # https://github.com/ganehag/pyMeterBus/blob/master/meterbus/core_objects.py
        #     code, vif_enh = _parse_vifx(record)
        #     print(f"code: {code:03d}/0x{code:02X}")
        #     meterbus.VIFUnit.DATE_TIME
        #     meterbus.VIFUnit.ENERGY_J
        #     meterbus.VIFUnit.POWER_W
        #     meterbus.VIFUnit.VOLUME
        #     print(record.interpreted)
        #     print("....")
        return


if __name__ == "__main__":
    asyncio.run(main())
