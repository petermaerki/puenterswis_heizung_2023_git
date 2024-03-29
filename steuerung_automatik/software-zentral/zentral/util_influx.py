import asyncio
import logging
from typing import Dict, List, Union
from aiohttp.client_exceptions import ClientConnectorError
from hsm import hsm
from influxdb_client import Point, DeleteApi
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from zentral.config_base import Haus

from zentral.config_secrets import InfluxSecrets
from zentral.util_constants_haus import SpPosition
from zentral.util_modbus_iregs_all import ModbusIregsAll

logger = logging.getLogger(__name__)


class InfluxRecords:
    def __init__(self, haus: Haus):
        self._dict_tags = {
            "position": haus.influx_tag,  # "haus_08", "zentral"
            "etappe": haus.config_haus.etappe.tag,  # "puent"
            "haus": haus.config_haus.nummer,
        }
        self._records: List[Dict] = []

    def add_fields(self, fields: Dict[str, Union[float, int]]):
        self._records.append(
            {"measurement": "Heizung", "tags": self._dict_tags, "fields": fields},
        )


class Influx:
    def __init__(self, etappe: str):
        secrets = InfluxSecrets()
        self._secrets = secrets
        self._etappe = etappe
        self._client = InfluxDBClientAsync(url=secrets.url, token=secrets.token, org=secrets.org)
        self._bucket = secrets.bucket
        self._api = self._client.write_api()

    async def close(self):
        await self._client.close()

    async def delete_bucket(self) -> None:
        # Delete all points from bucket
        delete_api = DeleteApi(self._client)
        await delete_api.delete(
            start="2020-01-01T00:00:00Z",
            stop="2060-01-01T00:00:00Z",
            predicate="",
            bucket=self._secrets.bucket,
        )
        logger.warning(f"Deleted Bucket {self._secrets.bucket}")

    async def write_records(self, records: InfluxRecords):
        try:
            success = await self._api.write(bucket=self._bucket, record=records._records)
            if not success:
                logger.error("Failed to write to influx")
        except ClientConnectorError:
            logger.exception("Failed to write to influx")
        except TimeoutError:
            logger.exception("Failed to write to influx")

    async def write_obsolete(self, haus: Haus, fields: Dict[str, Union[float, int]]):
        # version = await self._client.version()
        # logger.info(f"InfluxDB: {version}")

        dict_tags = {
            "position": haus.influx_tag,  # "haus_08", "zentral"
            "etappe": self._etappe,  # "puent"
            "haus": haus.config_haus.nummer,
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
            {"measurement": "Heizung", "tags": dict_tags, "fields": fields},
        ]
        success = await self._api.write(bucket=self._bucket, record=records)
        if not success:
            logger.error("Failed to write to influx")

    async def send_modbus_iregs_all(self, haus: "Haus", modbus_iregs_all: "ModbusIregsAll") -> None:
        r = InfluxRecords(haus=haus)
        fields: Dict[str, float] = {}
        for p in SpPosition:
            pair_ds18 = modbus_iregs_all.pairs_ds18[p.ds18_pair_index]
            fields[f"{p.tag}_error_C"] = pair_ds18.error_C
            if pair_ds18.error_any:
                continue
            fields[f"{p.tag}_temperature_C"] = pair_ds18.temperature_C
        r.add_fields(fields=fields)
        await self.write_records(records=r)

    async def send_hsm_dezental(self, haus: "Haus", state: hsm.HsmState) -> None:
        offset_total = 0.8
        anzahl_haeuser = len(haus.config_haus.etappe.dict_haeuser)
        offset = haus.config_haus.haus_idx0 * offset_total / max(1, (anzahl_haeuser - 1))
        state_value = state.value + offset
        # print(haus.influx_tag, state_value)
        r = InfluxRecords(haus=haus)
        r.add_fields(
            {
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
