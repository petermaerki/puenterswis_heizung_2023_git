import logging

from zentral.util_modbus_wrapper import ModbusWrapper

logger = logging.getLogger(__name__)


class PcbDezentralHeizzentrale:
    def __init__(self, modbus: "ModbusWrapper", modbus_address: int):
        assert isinstance(modbus, ModbusWrapper)
        self._modbus = modbus
        self._modbus_address = modbus_address
        self._modbus_label = f"PcbDezentralHeizzentrale(modbus={self._modbus_address})"

        self.Tsz1_C: float = 25.0
        self.Tsz2_C: float = 35.0
        self.Tsz3_C: float = 45.0
        self.Tsz4_C: float = 65.0

        self.Tfr_C: float = 25.0
        self.Tfv_C: float = 25.0

        self.Tkr_C: float = 25.0
        self.Tbv1_C: float = 25.0
        self.Tbv2_C: float = 25.0
        self.Tbv_C: float = 25.0

        self.Taussen: float = 18.0


"""
Todo:
Modbus
10	DS_0	Tkr
10	DS_1	Tkr
10	DS_2	Tbv1
10	DS_3	Tbv1
10	DS_4	Tbv2
10	DS_5	Tbv2
10	DS_6	Tbv
10	DS_7	Tbv
		
11	DS_0	Tsz1
11	DS_1	Tsz1
11	DS_2	Tsz2
11	DS_3	Tsz2
11	DS_4	Tsz3
11	DS_5	Tsz3
11	DS_6	Tsz4
11	DS_7	Tsz4
		
12	DS_0	Tfv
12	DS_1	Tfv
12	DS_2	Tfr
12	DS_3	Tfr
12	DS_4	Taussen
12	DS_5	Taussen

"""
