import time

import meterbus
import serial

address = 254
address = 75
address = 0x829690102D2C400D

secondary_address = '829690102D2C400D'

# See Multical 303, table 11.2.3.1
# X20-00-101: Standard Profile Yearly Target data
data_sequence=(
(1,60,'Heat energy E1'),
(2,63,'Cooling energy E3'),
(3,68,'Volume V1'),
(4,97,'Energy E8'),
(5,110,'Energy E9'),
(6,1004,'Operating hours'),
(7,175,'Error hour counter'),
(8,86,'t1 actual (2 decimals)'),
(9,87,'t2 actual (2 decimals)'),
(10,89,'t1-t2 diff. temp. (2 decimals)'),
(11,80,'Power E1/E3 actual'),
(12,143,'Power Max month'),
(13,74,'Flow V1 actual'),
(14,139,'Flow V1 max month'),
(15,369,'Info bits'),
(16,348,'Date and Time'),
(17,60,'Heat energy E1'),
(18,63,'Cooling energy E3'),
(19,63,'Cooling energy E3'),
(20,68,'Volume V1'),
(21,97,'Energy E8'),
(22,110,'Energy E9'),
# (23,128,'Power Max year'),
# (24,124,'Flow V1 max year'),
# (25,238,'Date and Time (logged)'),
)

def _parse_vifx(record):
        if len(record.vib.parts) == 0:
            return None, None, None, None

        vif = record.vib.parts[0]
        vife = record.vib.parts[1:]
        vif_enh = None

        if vif == meterbus.VIFUnit.FIRST_EXT_VIF_CODES.value:  # 0xFB
            code = (vife[0] & record.UNIT_MULTIPLIER_MASK) | 0x200

        elif vif == meterbus.VIFUnit.SECOND_EXT_VIF_CODES.value:  # 0xFD
            code = (vife[0] & record.UNIT_MULTIPLIER_MASK) | 0x100

        elif vif in [meterbus.VIFUnit.VIF_FOLLOWING.value]:  # 0x7C
            return (1, record.vib.customVIF.decodeASCII, meterbus.VIFUnit.VARIABLE_VIF, None)

        elif vif == 0xFC:
            #  && (vib->vife[0] & 0x78) == 0x70

            # Disable this for now as it is implicit
            # from 0xFC
            # if vif & vtf_ebm:
            code = vife[0] & record.UNIT_MULTIPLIER_MASK
            factor = 1

            if 0x70 <= code <= 0x77:
                factor = pow(10.0, (vife[0] & 0x07) - 6)
            elif 0x78 <= code <= 0x7B:
                factor = pow(10.0, (vife[0] & 0x03) - 3)
            elif code == 0x7D:
                factor = 1

            return (factor, record.vib.customVIF.decodeASCII,
                    meterbus.VIFUnit.VARIABLE_VIF, None)

            # // custom VIF
            # n = (vib->vife[0] & 0x07);
            # snprintf(buff, sizeof(buff), "%s %s", mbus_unit_prefix(n-6), vib->custom_vif);
            # return buff;
            # return (1, "FixME", "FixMe", None)

        elif vif & record.EXTENSION_BIT_MASK:
            code = (vif & record.UNIT_MULTIPLIER_MASK)
            vif_enh = vife[0] & record.UNIT_MULTIPLIER_MASK

        else:
            code = (vif & record.UNIT_MULTIPLIER_MASK)

        return code, vif_enh
        return (
            *meterbus.VIFTable.lut[code],
            meterbus.VIFTable.enh.get(vif_enh, meterbus.VIFUnitEnhExt.UNKNOWN_ENHANCEMENT) if vif_enh else None,
        )

def main():
    # https://m-bus.com/documentation-wired/05-data-link-layer
    # Since quiescence on the line corresponds to
    # a 1 (Mark), the start bit must be a Space, and the 
    # stop bit a Mark. In between the 
    # eight data bits and the 
    # even parity bit are transmitted, ensuring that at least every eleventh bit is a Mark.
    with serial.Serial(port='/dev/ttyACM2',baudrate= 2400,bytesize= 8,parity= 'E',stopbits= 1,timeout= 0.5) as ser: 
        meterbus.debug(False)


        for retry in range(5):
            print(f"retry {retry}")
            meterbus.send_select_frame(ser, secondary_address)
            data = meterbus.recv_frame(ser, 1)
            if data is None:
                continue
            frame = meterbus.load(data=data)

            time.sleep(0.2)
            meterbus.send_request_frame(ser, meterbus.ADDRESS_NETWORK_LAYER)
            time.sleep(0.2)

            data = meterbus.recv_frame(ser)
            if data is None:
                # time.sleep(0.2)
                continue
            assert isinstance(frame, meterbus.TelegramACK)
            frame = meterbus.load(data=data)
            assert isinstance(frame, meterbus.TelegramLong)
            print(type(frame))
            print(frame.to_JSON())
            records = frame.interpreted['body']['records']
            assert len(records) == 23 # Why not 25?
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
    main()
