import asyncio
import logging
import time
from typing import Dict, List, Union
from hsm import hsm
from influxdb_client import Point, DeleteApi, WriteOptions
from influxdb_client.client.influxdb_client import InfluxDBClient
from zentral.config_base import Haus

from zentral.config_secrets import InfluxSecrets
from zentral.util_constants_haus import SpPosition
from zentral.util_modbus_iregs_all import ModbusIregsAll

logger = logging.getLogger(__name__)


class InfluxRecords:
    """
    Add timestamp:
    See https://influxdb-client.readthedocs.io/en/latest/api.html#influxdb_client.WriteApi.write
    See https://powersj.io/posts/influxdb-client-python-write-api-deep-dive/#dictionary
    See https://docs.influxdata.com/influxdb/cloud/reference/syntax/line-protocol/#timestamp
    See https://docs.influxdata.com/influxdb/cloud/reference/glossary/#unix-timestamp
    """

    def __init__(self, haus: Haus):
        self._dict_tags = {
            "position": haus.influx_tag,  # "haus_08", "zentral"
            "etappe": haus.config_haus.etappe.tag,  # "puent"
            "haus": haus.config_haus.nummer,
        }
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
    def __init__(self, etappe: str):
        secrets = InfluxSecrets()
        self._secrets = secrets
        self._etappe = etappe
        self._client = InfluxDBClient(url=secrets.url, token=secrets.token, org=secrets.org)
        self._bucket = secrets.bucket
        write_options = WriteOptions(
            batch_size=500,  # [1] the number of data point to collect in batch
            flush_interval=10_000,  # [ms] flush data at least in this interval (milliseconds)
            jitter_interval=2_000,  # [ms] this is primarily to avoid large write spikes for users running a large number of client instances ie, a jitter of 5s and flush duration 10s means flushes will happen every 10-15s (milliseconds)
            retry_interval=5_000,  # [ms] the time to wait before retry unsuccessful write (milliseconds)
            max_retries=5,  # the number of max retries when write fails, 0 means retry is disabled
            max_retry_delay=30_000,  # [ms] the maximum delay between each retry attempt in milliseconds
            max_close_wait=30_000,  # [ms] the maximum time to wait for writes to be flushed if close() is called
            exponential_base=2,  # base for the exponential retry delay
        )
        self._api = self._client.write_api(write_options=write_options)
        self._api = self._client.write_api()
        # self.interval_haus_temperatures = UploadInterval(interval_s=1 * 60)

    async def close_and_flush(self):
        self._client.close()

    async def delete_bucket(self) -> None:
        # Delete all points from bucket
        delete_api = DeleteApi(self._client)
        predicate = "etappe=virgin"
        # predicate="",
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
            logger.exception("Failed to write to influx", e)
        # TODO: Test the error handling!
        # except ClientConnectorError:
        #     logger.exception("Failed to write to influx")
        # except TimeoutError:
        #     logger.exception("Failed to write to influx")

    async def send_modbus_iregs_all(self, haus: "Haus", modbus_iregs_all: "ModbusIregsAll") -> None:
        fields: Dict[str, float] = {}

        fields["uptime_s"] = modbus_iregs_all.uptime_s

        for p in SpPosition:
            pair_ds18 = modbus_iregs_all.pairs_ds18[p.ds18_pair_index]
            fields[f"{p.tag}_error_C"] = pair_ds18.error_C
            if pair_ds18.error_any:
                continue
            fields[f"{p.tag}_temperature_C"] = pair_ds18.temperature_C

        ladung_minimum = modbus_iregs_all.ladung_minimum(temperatur_aussen_C=-8.0)
        if ladung_minimum is not None:
            fields["ladung_baden_prozent"] = ladung_minimum.ladung_baden.ladung_prozent
            fields["ladung_heizung_prozent"] = ladung_minimum.ladung_heizung.ladung_prozent
            fields["ladung_minimum_prozent"] = ladung_minimum.ladung_prozent

        if haus.status_haus.interval_haus_temperatures.time_over:
            r = InfluxRecords(haus=haus)
            r.add_fields(fields=fields)
            await self.write_records(records=r)

    async def send_hsm_dezental(self, haus: "Haus", state: hsm.HsmState) -> None:
        offset_total = 0.8
        anzahl_haeuser = len(haus.config_haus.etappe.dict_haeuser)
        offset = haus.config_haus.haus_idx0 * offset_total / max(1, (anzahl_haeuser - 1))
        state_value = state.value + offset
        # print(haus.influx_tag, state_value)
        if haus.status_haus.interval_haus_hsm.time_over:
            r = InfluxRecords(haus=haus)
            r.add_fields(
                fields={
                    "hsm_state_value": state_value,
                    "modbus_ok_percent": haus.status_haus.hsm_dezentral.modbus_history.percent,
                }
            )
            await self.write_records(records=r)


class HsmInfluxLogger(hsm.HsmLoggerProtocol):
    def __init__(self, haus: Haus, grafana: Influx):
        self._haus = haus
        self._grafana = grafana

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
            await self._grafana.send_hsm_dezental(haus=self._haus, state=before)
            await self._grafana.send_hsm_dezental(haus=self._haus, state=after)

        asyncio.ensure_future(asyncfunc())


async def main():
    secrets = InfluxSecrets()

    async with InfluxDBClientAsync(
        url=secrets.url,
        token=secrets.token,
        org=secrets.org,
    ) as client:
        version = await client.version()
        print("\n------- Version -------\n")
        print(f"InfluxDB: {version}")
        write_api = client.write_api()

        """
            {
        "measurement": "pico_emil",  # a measurement has one 'measurement'. It is the name of the pcb.
        "fields": {
            "temperature_C": "23.5",
            "humidity_pRH": "88.2",
        },
        "tags": {
            "setup": "zeus",
            "room": "B15",
            "position": "hintenLinks",
            "user": "pmaerki",
        },
    },

"""

        dict_tags = {
            "position": "haus_08",  # "zentral"
            "etappe": "bochs",  # "puent"
            "haus": 8,
        }

        # Fields für Dezentral
        # sp_oben_temperatureC
        # sp_open_errorC
        # sp_mitte_temperatureC
        # sp_mitte_errorC
        # sp_unten_temperatureC
        # sp_unten_errorC
        # ventil_open

        # Fields fuer Zentral
        # Tbv1_C
        # energy_valve_open

        # records = [
        #     {"measurement": "haus-08-sp_oben", "tags": {"location": location}, "fields": {"temperature_C": 25.3}, "time": 1},
        #     {"measurement": "haus-08-sp_unten", "tags": {"location": location}, "fields": {"temperature_C": 21.3}, "time": 1},
        # ]
        records = [
            {"measurement": "Heizung", "tags": dict_tags, "fields": {"temperature_C": 25.3, "error_C": 20.0}},
            {"measurement": "Heizung", "tags": dict_tags, "fields": {"temperature_C": 21.3, "error_C": 1.0}},
        ]
        successfully = await write_api.write(bucket="heizung_puent", record=records)
        print(f" > successfully: {successfully}")
        return

        write_api = client.write_api()
        _point1 = Point("haus-08-sp_oben").tag("location", "Dezentral").tag("haus", 7).field("temperature_C", 25.3)
        _point2 = Point("haus-08-sp_mitte").tag("location", "Dezentral").tag("haus", 8).field("temperature_C", 24.3)
        successfully = await write_api.write(bucket="heizung_puent", record=[_point1, _point2])
        print(f" > successfully: {successfully}")

        return

        write_api = client.write_api()
        _point1 = Point("haus-08-sp_oben").tag("location", "Dezentral").tag("haus", 7).field("temperature_C", 25.3)
        _point2 = Point("haus-08-sp_mitte").tag("location", "Dezentral").tag("haus", 8).field("temperature_C", 24.3)
        successfully = await write_api.write(bucket="heizung_puent", record=[_point1, _point2])
        print(f" > successfully: {successfully}")

        return
        """
        Prepare data


        """
        print("\n------- Write data by async API: -------\n")

        write_api = client.write_api()
        _point1 = Point("async_m").tag("location", "Prague").field("temperature", 25.3)
        _point2 = Point("async_m").tag("location", "New York").field("temperature", 24.3)
        successfully = await write_api.write(bucket="my-bucket", record=[_point1, _point2])
        print(f" > successfully: {successfully}")


if __name__ == "__main__":
    asyncio.run(main())
