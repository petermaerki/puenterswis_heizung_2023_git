import dataclasses
import logging
import typing

from micropython.portable_modbus_registers import IREGS_ALL, EnumModbusRegisters, GpioBits
from pymodbus import ModbusException

from zentral.util_constants_haus import SpPosition
from zentral.util_influx import InfluxRecords
from zentral.util_modbus_gpio import ModbusIregsAll2
from zentral.util_modbus_wrapper import ModbusWrapper
from zentral.util_sp_ladung_zentral import SpLadung, SpLadungZentral
from zentral.util_uploadinterval import UploadInterval

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class MissingModbusDataException(Exception):
    pass


@dataclasses.dataclass
class DsPair:
    """
    Ein Klemmenpaar auf PCB Dezentral, das aber im Heizraum installiert ist.
    """

    sp_position: SpPosition
    label: str
    """
    Tbr_C, Tbv1_C, ...
    """


class PcbDezentral:
    def __init__(self, modbus_slave_addr: int, list_ds_pair: list[DsPair]) -> None:
        self.modbus_slave_addr = modbus_slave_addr

        self.list_ds_pair = list_ds_pair
        """
        The configured screw terminal pairs (Schraubklemmenpaar)
        """

        self.modbus_iregs_all2: ModbusIregsAll2 | None = None
        """
        The last result from modbus.
        None if no data received yet.
        None if last request failed.
        """

        self._dict_label_2_pair: dict[str, DsPair] = {}
        for pair in self.list_ds_pair:
            self._dict_label_2_pair[pair.label] = pair

    @property
    def modbus_label(self) -> str:
        return f"PcbDezentralHeizzentrale(modbus={self.modbus_slave_addr})"

    async def read(self, modbus: ModbusWrapper) -> None:
        """
        See also:
        async def handle_haus(self, haus: "Haus", grafana=Influx) -> bool:
        """
        assert isinstance(modbus, ModbusWrapper)

        try:
            rsp = await modbus.read_input_registers(
                slave=self.modbus_slave_addr,
                slave_label=self.modbus_label,
                address=EnumModbusRegisters.SETGET16BIT_ALL_SLOW,
                count=IREGS_ALL.register_count,
            )
        except ModbusException as e:
            self.modbus_iregs_all2 = None
            raise e from e

        self.modbus_iregs_all2 = ModbusIregsAll2(rsp.registers)

    async def write_gpio(self, modbus: ModbusWrapper, gpio: GpioBits) -> None:
        _rsp = await modbus.write_registers(
            slave=self.modbus_slave_addr,
            slave_label=self.modbus_label,
            address=EnumModbusRegisters.SETGET16BIT_GPIO,
            values=[gpio.value],
        )

    def get_temperature_C(self, label: str) -> float | None:
        """
        return None if both ds18 failed. See DS18_REDUNDANCY_FATAL_C.
        """
        if self.modbus_iregs_all2 is None:
            raise MissingModbusDataException(f"No modbus data address {self.modbus_slave_addr}!")

        pair = self._dict_label_2_pair[label]
        pair_ds18 = self.modbus_iregs_all2.get_ds18_pair(pair.sp_position)
        if pair_ds18.temperature_C is None:
            raise MissingModbusDataException(f"Error on DS18 '{pair.label}/SpPosition.{pair.sp_position.name}' error_C={pair_ds18.error_C:0.1f}C !")
        return pair_ds18.temperature_C


_DS0_DS1 = SpPosition.UNUSED
_DS2_DS3 = SpPosition.UNTEN
_DS4_DS5 = SpPosition.MITTE
_DS6_DS7 = SpPosition.OBEN


class PcbsDezentralHeizzentrale:
    def __init__(self, is_bochs: bool) -> None:
        self.dict_mock_temperatures_C: dict[str, float] | None = None
        self.interval_grafana = UploadInterval(interval_s=1 * 60)
        """
        if None: read temperatures via modbus
        Otherwise: mocked temperatures
        """
        self._ventilator_on = False

        self._pcb10 = PcbDezentral(
            modbus_slave_addr=10,
            list_ds_pair=[
                DsPair(_DS0_DS1, "Tbr_C"),
                DsPair(_DS2_DS3, "Tbv1_C"),
                DsPair(_DS4_DS5, "Tbv2_C"),
                DsPair(_DS6_DS7, "Tbv_C"),
            ],
        )
        self._pcb11 = PcbDezentral(
            modbus_slave_addr=11,
            list_ds_pair=[
                DsPair(_DS0_DS1, "Tfv_C"),
                DsPair(_DS2_DS3, "Tfr_C"),
                DsPair(_DS4_DS5, "TaussenU_C"),
                DsPair(_DS6_DS7, "TinnenA_C"),
            ],
        )
        self._pcb12 = PcbDezentral(
            modbus_slave_addr=12,
            list_ds_pair=[
                DsPair(_DS0_DS1, "Tsz1_C"),
                DsPair(_DS2_DS3, "Tsz2_C"),
                DsPair(_DS4_DS5, "Tsz3_C"),
                DsPair(_DS6_DS7, "Tsz4_C"),
            ],
        )

        self.pcbs: list[PcbDezentral] = [self._pcb10, self._pcb11, self._pcb12]

        if is_bochs:
            self._pcb13 = PcbDezentral(
                modbus_slave_addr=13,
                list_ds_pair=[
                    DsPair(_DS0_DS1, "TinnenB_C"),
                ],
            )
            self.pcbs.append(self._pcb13)

        self._dict_label_2_pcb: dict[str, PcbDezentral] = {}
        for pcb in self.pcbs:
            for pair in pcb.list_ds_pair:
                self._dict_label_2_pcb[pair.label] = pcb

    async def update_ventilator(self, modbus: ModbusWrapper) -> None:
        """
        Ventilator ein falls innen zu warm und aussen kuehler.
        """
        assert isinstance(modbus, ModbusWrapper)

        async def update(pcb: PcbDezentral, innen_C: float) -> None:
            hysterese_C = 2.0
            innen_zu_warm_C = 22.0
            differenz_innen_aussen_C = 2.0
            aussen_kuehler_C = innen_C - self.TaussenU_C
            ausschalten = innen_C < innen_zu_warm_C or aussen_kuehler_C < differenz_innen_aussen_C
            einschalten = innen_C > innen_zu_warm_C + hysterese_C and aussen_kuehler_C > differenz_innen_aussen_C + hysterese_C
            if ausschalten:
                self._ventilator_on = False
            if einschalten:
                self._ventilator_on = True
            gpio = GpioBits(0)
            gpio.relais_valve_open = self._ventilator_on
            await pcb.write_gpio(modbus=modbus, gpio=gpio)

        if modbus.context.config_etappe.is_bochs:
            await update(pcb=self._pcb10, innen_C=self.TinnenA_C)
            await update(pcb=self._pcb13, innen_C=self.TinnenB_C)
        else:
            await update(pcb=self._pcb11, innen_C=self.TinnenA_C)

    def __getattr__(self, attribute_name: str) -> float:
        """
        Calling 'x.Tfv' will call this method.
        'attribute_name' is set to 'x.Tfv'.

         throw MissingModbusDataException if no data received yet or communication is broken
        """
        if self.dict_mock_temperatures_C is not None:
            return self.dict_mock_temperatures_C[attribute_name]

        try:
            pcb = self._dict_label_2_pcb[attribute_name]
        except KeyError as e:
            raise KeyError(f"KeyError '{attribute_name}'! {','.join(sorted(self._dict_label_2_pcb))}") from e
        temperature_C = pcb.get_temperature_C(label=attribute_name)
        if temperature_C is None:
            raise MissingModbusDataException()
        return temperature_C

    def set_mock(self, dict_temperatures_C: dict[str, float]) -> None:
        for label in dict_temperatures_C:
            assert label in self._dict_label_2_pcb, f"Unknown label={label}! {','.join(self._dict_label_2_pcb)}"
        self.dict_mock_temperatures_C = dict_temperatures_C

    @property
    def _sp_ladung_zentral(self) -> SpLadungZentral:
        return SpLadungZentral(
            Tsz1_C=self.Tsz1_C,
            Tsz2_C=self.Tsz2_C,
            Tsz3_C=self.Tsz3_C,
            Tsz4_C=self.Tsz4_C,
        )

    @property
    def sp_ladung_zentral_prozent(self) -> float:
        return self._sp_ladung_zentral.ladung_prozent

    @property
    def sp_ladung_zentral(self) -> SpLadung:
        return self._sp_ladung_zentral.ladung

    async def send_influxdb(self, context: "Context") -> None:
        if not self.interval_grafana.time_over:
            return

        hsm_zentral = context.hsm_zentral
        anzahl_brenner_on = context.hsm_zentral.controller_master.handler_oekofen.anzahl_brenner_on
        pumpe_on = not hsm_zentral.relais.relais_6_pumpe_gesperrt

        fields: dict[str, float] = {}
        for pcb in self.pcbs:
            prefix_temperature = "zentral_temperature_"
            prefix_error = "zentral_error_"

            if hsm_zentral.is_state_drehschalterauto():
                if pumpe_on:
                    fields[prefix_temperature + "solltemperatur_Tfv_C"] = hsm_zentral.controller_master.handler_last.solltemperatur_Tfv_C

            for ds_pair in pcb.list_ds_pair:
                assert pcb.modbus_iregs_all2 is not None
                pair_ds18 = pcb.modbus_iregs_all2.get_ds18_pair(ds_pair.sp_position)
                if pair_ds18.temperature_C is not None:
                    fields[prefix_temperature + ds_pair.label] = pair_ds18.temperature_C
                if pair_ds18.error_C is not None:
                    fields[prefix_error + ds_pair.label] = pair_ds18.error_C

        if anzahl_brenner_on > 0:
            fields[prefix_temperature + "Tbr_brand_C"] = self.Tbr_C

        if pumpe_on:
            fields[prefix_temperature + "Tfv_pumpe_C"] = self.Tfv_C
            fields[prefix_temperature + "Tfr_pumpe_C"] = self.Tfr_C

        r = InfluxRecords(ctx=context)
        r.add_fields(fields=fields)
        await context.influx.write_records(records=r)
