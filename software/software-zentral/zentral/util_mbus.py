from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import enum
import logging
import time
import typing
from decimal import Decimal

import meterbus  # type: ignore[import]
import serial  # type: ignore[import]
from meterbus import MeasureUnit, VIFUnit

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, repr=True)
class MbusMeasurementSpec:
    datasheet_no: int
    datasheet_register_id: int
    datasheet_register_name: str
    no: int | None = None
    expected_python_type: type | None = None
    tag: str | None = None
    expected_type: VIFUnit | None = None
    expected_unit: MeasureUnit | None = None

    def __post_init__(self) -> None:
        assert isinstance(self.datasheet_no, int)
        assert isinstance(self.datasheet_register_id, int)
        assert isinstance(self.datasheet_register_name, str)
        assert isinstance(self.no, int | None)
        assert isinstance(self.expected_python_type, type | None)
        assert isinstance(self.tag, str | None)
        assert isinstance(self.expected_type, VIFUnit | None)
        assert isinstance(self.expected_unit, MeasureUnit | None)

    @property
    def expected_type_str(self) -> str:
        assert self.expected_type is not None
        return self._enum_as_str(self.expected_type)

    @property
    def expected_unit_str(self) -> str:
        assert self.expected_unit is not None
        return self._enum_as_str(self.expected_unit)

    @staticmethod
    def _enum_as_str(v: enum.Enum) -> str:
        return f"{v.__class__.__name__}.{v.name}"


_MBUS_MEASUREMENT_VALUES: list[MbusMeasurementSpec] = [
    # 1
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.ENERGY_WH,
    # unit: MeasureUnit.WH,
    # value: 4000
    MbusMeasurementSpec(1, 60, "Heat energy E1", 1, int, "energy_heating_E1_Wh", VIFUnit.ENERGY_WH, MeasureUnit.WH),
    # 2
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.ENERGY_WH,
    # unit: MeasureUnit.WH,
    # unit_enh: VIFUnitEnhExt.NEGATIVE_ACCUMULATION,
    # value: 0
    MbusMeasurementSpec(2, 63, "Cooling energy E3", 2, int, "energy_cooling_E3_Wh", VIFUnit.ENERGY_WH, MeasureUnit.WH),
    # 3
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.VOLUME,
    # unit: MeasureUnit.M3,
    # value: 0.41000000000000003108624468950438313186168670654296875
    MbusMeasurementSpec(3, 68, "Volume V1", 3, Decimal, "volume_m3", VIFUnit.VOLUME, MeasureUnit.M3),
    # 4
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.MANUFACTURER_SPEC,
    # unit: MeasureUnit.NONE,
    # unit_enh: VIFUnitEnhExt.UNKNOWN_ENHANCEMENT,
    # value: 23
    MbusMeasurementSpec(4, 97, "Energy E8", 4, Decimal, "energy_E8_XXX", VIFUnit.MANUFACTURER_SPEC, MeasureUnit.NONE),
    # 5
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.MANUFACTURER_SPEC,
    # unit: MeasureUnit.NONE,
    # unit_enh: VIFUnitEnhExt.UNKNOWN_ENHANCEMENT,
    # value: 20
    MbusMeasurementSpec(5, 110, "Energy E9", 5, Decimal, "energy_E9_XXX", VIFUnit.MANUFACTURER_SPEC, MeasureUnit.NONE),
    # 6
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.ON_TIME,
    # unit: MeasureUnit.SECONDS,
    # value: 14029200
    MbusMeasurementSpec(6, 1004, "Operating hours", 6, int, "operating_hours_s", VIFUnit.ON_TIME, MeasureUnit.SECONDS),
    # 7
    # function: FunctionType.ERROR_STATE_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.ON_TIME,
    # unit: MeasureUnit.SECONDS,
    # value: 0
    MbusMeasurementSpec(7, 175, "Error hour counter", 7, int, "error_hours_s", VIFUnit.ON_TIME, MeasureUnit.SECONDS),
    # 8
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.FLOW_TEMPERATURE,
    # unit: MeasureUnit.C,
    # value: 41.02000000000000312638803734444081783294677734375
    MbusMeasurementSpec(8, 86, "t1 actual (2 decimals)", 8, Decimal, "temperature_t1_C", VIFUnit.FLOW_TEMPERATURE, MeasureUnit.C),
    # 9
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.RETURN_TEMPERATURE,
    # unit: MeasureUnit.C,
    # value: 22.400000000000002131628207280300557613372802734375
    MbusMeasurementSpec(9, 87, "t2 actual (2 decimals)", 9, Decimal, "temperature_t2_C", VIFUnit.RETURN_TEMPERATURE, MeasureUnit.C),
    # 10
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.TEMPERATURE_DIFFERENCE,
    # unit: MeasureUnit.K,
    # value: 18.620000000000000994759830064140260219573974609375
    MbusMeasurementSpec(10, 89, "t1-t2 diff. temp. (2 decimals)", 10, Decimal, "temperature_t1_minus_t2_C", VIFUnit.TEMPERATURE_DIFFERENCE, MeasureUnit.K),
    # 11
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.POWER_W,
    # unit: MeasureUnit.W,
    # value: 0
    MbusMeasurementSpec(11, 80, "Power E1/E3 actual", 11, int, "power_W", VIFUnit.POWER_W, MeasureUnit.W),
    # 12
    # function: FunctionType.MAXIMUM_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.POWER_W,
    # unit: MeasureUnit.W,
    # value: 1300
    MbusMeasurementSpec(12, 143, "Power Max month"),
    # 13
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.VOLUME_FLOW,
    # unit: MeasureUnit.M3_H,
    # value: 0
    MbusMeasurementSpec(13, 74, "Flow V1 actual", 13, Decimal, "flow_v1_m3h", VIFUnit.VOLUME_FLOW, MeasureUnit.M3_H),
    # 14
    # function: FunctionType.MAXIMUM_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.VOLUME_FLOW,
    # unit: MeasureUnit.M3_H,
    # value: 0.0980000000000000037747582837255322374403476715087890625
    MbusMeasurementSpec(14, 139, "Flow V1 max month"),
    # 15
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 0,
    # mbus_type: VIFUnit.MANUFACTURER_SPEC,
    # unit: MeasureUnit.NONE,
    # unit_enh: VIFUnitEnhExt.PER_HOUR,
    # value: 0
    MbusMeasurementSpec(15, 369, "Info bits"),
    MbusMeasurementSpec(16, 348, "Date and Time"),
    # 16
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 1,
    # mbus_type: VIFUnit.ENERGY_WH,
    # unit: MeasureUnit.WH,
    # value: 0
    MbusMeasurementSpec(17, 60, "Heat energy E1"),
    MbusMeasurementSpec(18, 63, "Cooling energy E3"),
    MbusMeasurementSpec(19, 63, "Cooling energy E3"),
    MbusMeasurementSpec(18, 68, "Volume V1"),
    MbusMeasurementSpec(21, 97, "Energy E8"),
    MbusMeasurementSpec(22, 110, "Energy E9"),
    MbusMeasurementSpec(23, 128, "Power Max year"),
    MbusMeasurementSpec(24, 124, "Flow V1 max year"),
    MbusMeasurementSpec(25, 238, "Date and Time (logged)"),
    # 17
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 1,
    # mbus_type: VIFUnit.ENERGY_WH,
    # unit: MeasureUnit.WH,
    # unit_enh: VIFUnitEnhExt.NEGATIVE_ACCUMULATION,
    # value: 0
    # 18
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 1,
    # mbus_type: VIFUnit.VOLUME,
    # unit: MeasureUnit.M3,
    # value: 0
    # 19
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 1,
    # mbus_type: VIFUnit.MANUFACTURER_SPEC,
    # unit: MeasureUnit.NONE,
    # unit_enh: VIFUnitEnhExt.UNKNOWN_ENHANCEMENT,
    # value: 0
    # 20
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 1,
    # mbus_type: VIFUnit.MANUFACTURER_SPEC,
    # unit: MeasureUnit.NONE,
    # unit_enh: VIFUnitEnhExt.UNKNOWN_ENHANCEMENT,
    # value: 0
    # 21
    # function: FunctionType.MAXIMUM_VALUE,
    # storage_number: 1,
    # mbus_type: VIFUnit.POWER_W,
    # unit: MeasureUnit.W,
    # value: 0
    # 22
    # function: FunctionType.MAXIMUM_VALUE,
    # storage_number: 1,
    # mbus_type: VIFUnit.VOLUME_FLOW,
    # unit: MeasureUnit.M3_H,
    # value: 0
    # 23
    # function: FunctionType.INSTANTANEOUS_VALUE,
    # storage_number: 1,
    # mbus_type: VIFUnit.DATE,
    # unit: MeasureUnit.DATE,
    # value: 2024-07-01
]
"""
See Multical 303, table 11.2.3.1
X20-00-101: Standard Profile Yearly Target data
"""


class MBus:
    MAX_DURATION_SERIAL_READ = 0.2
    """
    Serial read is blocking: Therefor we tune the sleeps, which are non blocking, so that
    the read does not take longer than _MAX_DURATION_SERIAL_READ.
    If the read takes longer, the sleep before has to be incremented!
    """

    def __init__(self, port: str) -> None:
        # https://m-bus.com/documentation-wired/05-data-link-layer
        # Since quiescence on the line corresponds to
        # a 1 (Mark), the start bit must be a Space, and the
        # stop bit a Mark. In between the
        # eight data bits and the
        # even parity bit are transmitted, ensuring that at least every eleventh bit is a Mark.
        self.serial = serial.Serial(port=port, baudrate=2400, bytesize=8, parity="E", stopbits=1, timeout=0.4)
        meterbus.debug(False)

    async def read_mulical303_or_None(self, address: str, relais_valve_open: bool) -> MBusMeasurement | None:
        try:
            return await self.read_mulical303(address=address, relais_valve_open=relais_valve_open)
        except meterbus.exceptions.MBusFrameDecodeError as e:
            logger.debug(f"Failed to read mbus address {address}: {e}")
            return None

    async def read_mulical303(self, address: str, relais_valve_open: bool) -> MBusMeasurement:
        assert isinstance(address, str)
        assert isinstance(relais_valve_open, bool)
        secondary_address = address + "2D2C400D"
        assert len(secondary_address) == 16

        meterbus.debug(False)

        meterbus.send_select_frame(self.serial, secondary_address)
        await asyncio.sleep(0.08)
        with self.duration("A"):
            data = meterbus.recv_frame(self.serial, 1)
        frame = meterbus.load(data=data)

        await asyncio.sleep(0.2)
        meterbus.send_request_frame(self.serial, meterbus.ADDRESS_NETWORK_LAYER)
        await asyncio.sleep(0.7)

        with self.duration("B"):
            data = meterbus.recv_frame(self.serial)
        assert isinstance(frame, meterbus.TelegramACK)
        frame = meterbus.load(data=data)
        assert isinstance(frame, meterbus.TelegramLong)
        # print(frame.to_JSON())

        records = frame.interpreted["body"]["records"]
        return MBusMeasurement.factory(records=records, time_s=time.time(), relais_valve_open=relais_valve_open)

    @contextlib.contextmanager
    def duration(self, tag: str):
        begin_s = time.monotonic()
        yield
        duration_s = time.monotonic() - begin_s
        if duration_s > self.MAX_DURATION_SERIAL_READ:
            level = "WARNING: "
        else:
            level = ""
        logger.debug(f"{level}{tag}: {duration_s:0.2f}s")


@dataclasses.dataclass(frozen=True, repr=True)
class MBusMeasurement:
    time_s: float
    relais_valve_open: bool
    energy_heating_E1_Wh: float
    energy_cooling_E3_Wh: float
    volume_m3: float
    energy_E8_XXX: float
    energy_E9_XXX: float
    operating_hours_s: float
    error_hours_s: float
    temperature_t1_C: float
    temperature_t2_C: float
    temperature_t1_minus_t2_C: float
    power_W: float
    flow_v1_m3h: float

    def influx_fields(self, prefix: str) -> dict[str, typing.Any]:
        dict_influx: dict[str, typing.Any] = {
            prefix + "energy_E1_minus_E3_Wh": self.energy_E1_minus_E3_Wh,
        }
        for field in dataclasses.fields(self.__class__):
            if field.name == "time_s":
                # influxdb will add its own timestamp
                continue
            value = getattr(self, field.name)
            dict_influx[prefix + field.name] = value
        return dict_influx

    @property
    def energy_E1_minus_E3_Wh(self) -> float:
        return self.energy_heating_E1_Wh - self.energy_cooling_E3_Wh

    @staticmethod
    def factory(records: list[dict[str, str]], time_s: float, relais_valve_open: bool) -> MBusMeasurement:
        vargs: dict[str, float] = {}
        for measurement in _MBUS_MEASUREMENT_VALUES:
            if measurement.no is None:
                continue
            record = records[measurement.no - 1]

            # pylint: disable=C0123  # Use isinstance() rather than type() for a typecheck. (unidiomatic-typecheck)
            assert record["type"] == measurement.expected_type_str
            assert record["unit"] == measurement.expected_unit_str
            value = record["value"]
            assert type(value) is measurement.expected_python_type
            # print(f"*** {measurement.tag}: {value}")
            assert measurement.tag is not None
            vargs[measurement.tag] = float(value)

        return MBusMeasurement(time_s=time_s, relais_valve_open=relais_valve_open, **vargs)


async def main():
    secondary_address = "82969010"
    secondary_address = "83003675"

    mbus = MBus(port="/dev/ttyACM2")
    measurement = await mbus.read_mulical303(address=secondary_address, relais_valve_open=True)
    print(measurement.influx_fields("dezentral_mbus_"))


if __name__ == "__main__":
    asyncio.run(main())
