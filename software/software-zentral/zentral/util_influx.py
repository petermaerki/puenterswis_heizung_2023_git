import asyncio
import logging
import time
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from hsm import hsm  # type: ignore[import]
from influxdb_client import DeleteApi, WriteOptions  # type: ignore[import]
from influxdb_client.client.influxdb_client import InfluxDBClient  # type: ignore[import]

from zentral.config_base import Haus
from zentral.config_secrets import InfluxSecrets
from zentral.constants import DEVELOPMENT, ETAPPE_TAG_VIRGIN, TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT
from zentral.util_constants_haus import SpPosition
from zentral.util_ds18_pairs import DS18
from zentral.util_mbus import MBusMeasurement
from zentral.util_modbus_iregs_all import ModbusIregsAll
from zentral.util_modbus_oekofen import OekofenRegisters

if TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)

if DEVELOPMENT:
    INFLUX_FLASH_INTERVAL_MS = 10_000
else:
    INFLUX_FLASH_INTERVAL_MS = 60_000


class ValueObserver:
    def __init__(self) -> None:
        self.value: float = 0.0

    def changed(self, value: float) -> bool:
        """
        Return True if changed
        """
        if abs(self.value - value) < 0.01:
            return False

        self.value = value
        return True


class InfluxRecords:
    """
    Add timestamp:
    See https://influxdb-client.readthedocs.io/en/latest/api.html#influxdb_client.WriteApi.write
    See https://powersj.io/posts/influxdb-client-python-write-api-deep-dive/#dictionary
    See https://docs.influxdata.com/influxdb/cloud/reference/syntax/line-protocol/#timestamp
    See https://docs.influxdata.com/influxdb/cloud/reference/glossary/#unix-timestamp
    """

    def __init__(self, haus: Haus | None = None, ctx: "Optional[Context]" = None):
        if haus is not None:
            assert ctx is None
            etappe = haus.config_haus.etappe
            influx_tag = haus.influx_tag
        else:
            assert ctx is not None
            etappe = ctx.config_etappe
            influx_tag = "zentral"

        self._dict_tags = {
            "position": influx_tag,  # "haus_08", "zentral"
            "etappe": etappe.tag,  # "puent"
        }
        if haus is not None:
            self._dict_tags["haus"] = str(haus.config_haus.nummer)
            self._dict_tags["reihe"] = haus.config_haus.hausreihe.influx_reihe
        self._records: List[Dict] = []

    def add_fields(self, fields: Dict[str, Union[float, int]]):
        self._records.append(
            {
                "measurement": "Heizung",
                "tags": self._dict_tags,
                "fields": fields,
                "time": time.time_ns(),
            }
        )


class Influx:
    def __init__(self) -> None:
        secrets = InfluxSecrets()
        self._secrets = secrets
        self._client = InfluxDBClient(url=secrets.url, token=secrets.token, org=secrets.org)
        self._bucket = secrets.bucket
        write_options = WriteOptions(
            batch_size=500,  # [1] the number of data point to collect in batch
            flush_interval=INFLUX_FLASH_INTERVAL_MS,  # [ms] flush data at least in this interval (milliseconds)
            jitter_interval=2_000,  # [ms] this is primarily to avoid large write spikes for users running a large number of client instances ie, a jitter of 5s and flush duration 10s means flushes will happen every 10-15s (milliseconds)
            retry_interval=60_000,  # [ms] the time to wait before retry unsuccessful write (milliseconds)
            max_retries=1_000,  # the number of max retries when write fails, 0 means retry is disabled
            max_retry_delay=30_000,  # [ms] the maximum delay between each retry attempt in milliseconds
            max_close_wait=30_000,  # [ms] the maximum time to wait for writes to be flushed if close() is called
            exponential_base=2,  # base for the exponential retry delay
        )
        self._api = self._client.write_api(write_options=write_options)

        self.mbus_energy_E1_minus_E3_Wh = ValueObserver()
        self.mbus_power_W = ValueObserver()

    def close_and_flush(self):
        self._client.close()

    async def delete_bucket_virgin(self) -> None:
        await self.delete_bucket(predicate=f"etappe={ETAPPE_TAG_VIRGIN}")

    async def delete_bucket(self, predicate) -> None:
        # Delete all points from bucket
        delete_api = DeleteApi(self._client)
        delete_api.delete(
            start="2020-01-01T00:00:00Z",
            stop="2060-01-01T00:00:00Z",
            predicate=predicate,
            bucket=self._secrets.bucket,
        )
        logger.warning(f"Deleted Bucket {self._secrets.bucket}, prediacte '{predicate}'")

    async def write_records(self, records: InfluxRecords):
        try:
            self._api.write(bucket=self._bucket, record=records._records)
        except Exception as e:
            logger.exception("Failed to write to influx", exc_info=e)
        # TODO: Test the error handling!
        # except ClientConnectorError:
        #     logger.exception("Failed to write to influx")
        # except TimeoutError:
        #     logger.exception("Failed to write to influx")

    async def send_modbus_iregs_all(self, haus: Haus, modbus_iregs_all: "ModbusIregsAll", temperatur_aussen_C: float) -> None:
        if not haus.status_haus.interval_haus_temperatures.time_over:
            return

        fields: Dict[str, float] = {}

        fields["uptime_s"] = modbus_iregs_all.uptime_s

        for p in SpPosition:
            if p is SpPosition.UNUSED:
                continue
            pair_ds18 = modbus_iregs_all.pairs_ds18[p.ds18_pair_index]
            if pair_ds18.temperature_C is not None:
                fields[f"{p.tag}_temperature_C"] = pair_ds18.temperature_C
            if pair_ds18.error_C is not None:
                fields[f"{p.tag}_error_C"] = pair_ds18.error_C

            def add(ab: str, ds18: DS18) -> None:
                if ds18.ds18_ok_percent == 100:
                    # Do not flood grafana with 100 percent values.
                    # The legend will now just contain the sensors with errors!
                    return
                fields[f"{p.tag}_{ab}_ok_percent"] = ds18.ds18_ok_percent

            add("a", pair_ds18.a)
            add("b", pair_ds18.b)

        ladung_minimum = modbus_iregs_all.ladung_minimum(temperatur_aussen_C=temperatur_aussen_C)
        if ladung_minimum is not None:
            if not ladung_minimum.ladung_bodenheizung.is_sommer:
                fields["ladung_heizung_prozent"] = ladung_minimum.ladung_bodenheizung.ladung_prozent
            fields["ladung_baden_prozent"] = ladung_minimum.ladung_baden.ladung_prozent
            fields["ladung_minimum_prozent"] = ladung_minimum.ladung_prozent

        r = InfluxRecords(haus=haus)
        r.add_fields(fields=fields)
        await self.write_records(records=r)

    async def send_hsm_dezental(self, ctx: "Context", haus: Haus) -> None:
        r = InfluxRecords(haus=haus)
        hsm_dezentral = haus.status_haus.hsm_dezentral
        influx_offset08 = haus.config_haus.influx_offset05
        fields = {}
        fields["hsm_state_value"] = haus.status_haus.hsm_dezentral.get_state().value + influx_offset08
        fields["next_legionellen_kill_d"] = hsm_dezentral.next_legionellen_kill_s / 24.0 / 3600.0
        if hsm_dezentral.modbus_history.percent < 100:
            # Do not flood grafana with 100 percent values.
            # The legend will now just contain the sensors with errors!
            fields["modbus_ok_percent"] = hsm_dezentral.modbus_history.percent

        if ctx.hsm_zentral.is_state_drehschalterauto():
            try:
                if hsm_dezentral.modbus_iregs_all is not None:
                    v = haus.config_haus.hausreihe.grafana * int(hsm_dezentral.modbus_iregs_all.relais_gpio.relais_valve_open)
                    fields["relais_valve_open"] = v
                    fields["relais_valve_open_float"] = v + influx_offset08
            except AttributeError:
                pass

        if True:
            haus_ladung = hsm_dezentral.haus_ladung
            if haus_ladung is not None:
                fields["ladung_individuell_prozent"] = haus_ladung.ladung_individuell_prozent

        r.add_fields(fields=fields)
        await self.write_records(records=r)

    async def send_mbus_sum(self, ctx: "Context"):
        r = InfluxRecords(ctx=ctx)
        fields = {
            "sp_verbrauch_median_W": ctx.sp_verbrauch_median_W(time_s=time.time()),
        }
        r.add_fields(fields=fields)

        def mbus_sum():
            energy_E1_minus_E3_Wh = 0.0
            power_W = 0.0
            for haus in ctx.config_etappe.haeuser:
                mbus_measurement = haus.status_haus.hsm_dezentral.mbus_measurement
                if mbus_measurement is None:
                    # Sum will not be valid if one Haus is missing.
                    return
                energy_E1_minus_E3_Wh += mbus_measurement.energy_E1_minus_E3_Wh
                power_W += mbus_measurement.power_W

            if self.mbus_energy_E1_minus_E3_Wh.changed(energy_E1_minus_E3_Wh):
                fields["mbus_sum_energy_E1_minus_E3_Wh"] = energy_E1_minus_E3_Wh

            if self.mbus_power_W.changed(power_W):
                fields["mbus_sum_power_W"] = power_W

        mbus_sum()
        await self.write_records(records=r)

    async def send_mbus_haus(self, haus: Haus, mbus_measurement: MBusMeasurement) -> None:
        r = InfluxRecords(haus=haus)
        r.add_fields(fields=mbus_measurement.influx_fields("mbus_dezentral_"))
        await self.write_records(records=r)

    async def send_hsm_zentral(self, ctx: "Context") -> None:
        r = InfluxRecords(ctx=ctx)
        fields = {
            "hsm_zentral_state_value": ctx.hsm_zentral.get_state().value,
        }
        r.add_fields(fields=fields)

        def actiontimer():
            controller_master = ctx.hsm_zentral.controller_master
            controller_master.influxdb_add_fields(fields=fields)

            handler_last = controller_master.handler_last
            effective_valve_open_count = ctx.hsm_zentral.get_haeuser_ladung().effective_valve_open_count
            if not TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT:
                fields["target_valve_open_count"] = handler_last.target_valve_open_count + 0.1
            fields["effective_valve_open_count"] = effective_valve_open_count + 0.2
            fields["sp_zentral_steigung"] = controller_master.handler_sp_zentral.grafana

        def hausreihen():
            for hausreihe, energie_J in ctx.config_etappe.hausreihen.calculate(now_s=time.monotonic()).items():
                fields[f"hausreihe_{hausreihe.label}_fernleitung_energie_kWh"] = energie_J / 1000.0 / 3600.0

        def haeuser_ladung_minimum_prozent():
            minimum, avg = ctx.hsm_zentral.tuple_haeuser_ladung_minimum_prozent
            if minimum is not None:
                fields["haeuser_ladung_minimum_prozent"] = minimum
                fields["haeuser_ladung_avg_prozent"] = avg
                fields["haeuser_ladung_avg_soll_prozent"] = ctx.hsm_zentral.controller_master.haeuser_ladung_avg_soll_prozent

        def oekofen_summary():
            controller_master = ctx.hsm_zentral.controller_master
            val1, val2 = controller_master.handler_oekofen.brenner_uebersicht_prozent
            fields["brenner_1_uebersicht_prozent"] = val1 + 0.0
            fields["brenner_2_uebersicht_prozent"] = val2 + 0.3

            if ctx.hsm_zentral.is_state_drehschalterauto():
                for brenner in controller_master.handler_oekofen.modulation_soll.zwei_brenner:
                    fields[f"_brenner_{brenner.idx0+1}_modulation_soll_prozent"] = float(brenner.modulation.prozent) + brenner.idx0 * 0.3

            betrieb_notheizung = controller_master.handler_oekofen.betrieb_notheizung
            if betrieb_notheizung:
                betrieb_notheizung_prozent = 100
                betrieb_notheizung_prozent += int(ctx.hsm_zentral.relais.relais_1_elektro_notheizung)  # Relais state
                betrieb_notheizung_prozent += 1  # 1: Do not overlap in grafana with other values at 100%
                fields["betrieb_notheizung_prozent"] = betrieb_notheizung_prozent

        def mischventil_registers():
            registers = ctx.hsm_zentral.modbus_mischventil_registers
            if registers is None:
                return
            fields["mischventil_power_W"] = registers.heating_power_W - registers.cooling_power_W
            fields["mischventil_fluss_m3_h"] = 3600.0 * registers.fluss_m3_s
            fields["mischventil_energy_Wh"] = (registers.heating_energie_J - registers.cooling_energie_J) / 3600.0

        def mischventil_automatik():
            def overwrite(key: str, relais: bool, overwrite: tuple[bool, bool]) -> None:
                fields[key] = int(relais)
                manuell, relais_x = overwrite
                if manuell:
                    fields[key + "_overwrite"] = int(relais_x)

            overwrite(
                key="relais_0_mischventil_automatik",
                relais=ctx.hsm_zentral.relais.relais_0_mischventil_automatik,
                overwrite=ctx.hsm_zentral.relais.relais_0_mischventil_automatik_overwrite,
            )
            if ctx.hsm_zentral.is_state_drehschalterauto():
                fields["relais_1_elektro_notheizung"] = int(ctx.hsm_zentral.relais.relais_1_elektro_notheizung)
                fields["relais_2_brenner1_sperren"] = int(ctx.hsm_zentral.relais.relais_2_brenner1_sperren)
                fields["relais_3_brenner1_anforderung"] = int(ctx.hsm_zentral.relais.relais_3_brenner1_anforderung)
                fields["relais_4_brenner2_sperren"] = int(ctx.hsm_zentral.relais.relais_4_brenner2_sperren)
                fields["relais_5_brenner2_anforderung"] = int(ctx.hsm_zentral.relais.relais_5_brenner2_anforderung)
            overwrite(
                key="relais_6_pumpe_gesperrt",
                relais=ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt,
                overwrite=ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt_overwrite,
            )
            # fields["relais_7_automatik"]=int(ctx.hsm_zentral.relais.relais_7_automatik)

        def mischventil_stellwert_100():
            key = "mischventil_stellwert_100"
            if ctx.hsm_zentral.is_state_drehschalterauto():
                fields[key] = ctx.hsm_zentral.mischventil_stellwert_100
            manuell, mischventil_stellwert_100 = ctx.hsm_zentral.mischventil_stellwert_100_overwrite
            if manuell:
                fields[key + "_overwrite"] = mischventil_stellwert_100

        def mischventil_credit():
            credit_100 = ctx.hsm_zentral.controller_mischventil.get_credit_100()
            if credit_100 is None:
                return
            if ctx.hsm_zentral.is_state_drehschalterauto():
                fields["mischventil_credit_100"] = credit_100

        def pumpe():
            key = "hsm_zentral_pumpe_ein"
            if ctx.hsm_zentral.is_state_drehschalterauto():
                fields[key] = int(not ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt)
            manuell, relais_6_pumpe_gesperrt = ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt_overwrite
            if manuell:
                fields[key + "_overwrite"] = int(not relais_6_pumpe_gesperrt)

        def ladung_zentral():
            pcbs = ctx.modbus_communication.pcbs_dezentral_heizzentrale
            fields["sp_ladung_zentral_prozent"] = pcbs.sp_ladung_zentral_prozent
            # fields["sp_ladung_zentral_level_prozent"] = pcbs.sp_ladung_zentral.lower_level_prozent

        if ctx.hsm_zentral.is_state_drehschalterauto():
            actiontimer()
            hausreihen()
            mischventil_automatik()
            mischventil_stellwert_100()
            mischventil_credit()
            pumpe()
        mischventil_registers()
        haeuser_ladung_minimum_prozent()
        oekofen_summary()
        ladung_zentral()
        await self.write_records(records=r)

    async def send_oekofen(self, ctx: "Context", modbus_oekofen_registers: OekofenRegisters) -> None:
        r = InfluxRecords(ctx=ctx)
        prefix = "temp_oekofen_"
        r.add_fields(fields=modbus_oekofen_registers.get_influx_fields(prefix))
        r.add_fields(fields={prefix + "FA_STARTS": modbus_oekofen_registers.fa_starts()})
        await self.write_records(records=r)


class HsmDezentralInfluxLogger(hsm.HsmLoggerProtocol):
    def __init__(self, influx: Influx, ctx: "Context", haus: Haus):
        assert isinstance(influx, Influx)
        assert isinstance(haus, Haus)
        self._influx = influx
        self._ctx = ctx
        self._haus = haus

    def fn_log_debug(self, msg: str) -> None:
        pass

    def fn_log_info(self, msg: str) -> None:
        pass

    def fn_state_change(
        self,
        before: hsm.HsmState,
        after: hsm.HsmState,
        why: str,
        list_entry_exit: List[str],
    ) -> None:
        if before == after:
            return

        async def asyncfunc():
            # await self._influx.send_hsm_dezental(haus=self._haus, state=before)
            await self._influx.send_hsm_dezental(ctx=self._ctx, haus=self._haus)

        asyncio.ensure_future(asyncfunc())


class HsmZentralInfluxLogger(hsm.HsmLoggerProtocol):
    def __init__(self, influx: Influx, ctx: "Context"):
        assert isinstance(influx, Influx)
        self._influx = influx
        self._ctx = ctx

    def fn_log_debug(self, msg: str) -> None:
        pass

    def fn_log_info(self, msg: str) -> None:
        pass

    def fn_state_change(
        self,
        before: hsm.HsmState,
        after: hsm.HsmState,
        why: str,
        list_entry_exit: List[str],
    ) -> None:
        if before == after:
            return

        async def asyncfunc():
            # await self._influx.send_hsm_zentral(ctx=self._ctx, state=before)
            await self._influx.send_hsm_zentral(ctx=self._ctx)

        asyncio.ensure_future(asyncfunc())
