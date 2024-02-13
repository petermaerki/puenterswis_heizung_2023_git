import asyncio
import logging
from typing import Dict, List

from influxdb_client import Point
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from zentral.config_base import Haus

from zentral.config_secrets import InfluxSecrets
from zentral.util_modbus_iregs_all import ModbusIregsAll

logger = logging.getLogger(__name__)


class Grafana:
    def __init__(self, etappe: str):
        secrets = InfluxSecrets(etappe=etappe)
        self._etappe = etappe
        self._client = InfluxDBClientAsync(url=secrets.url, token=secrets.token, org=secrets.org)
        self._bucket = secrets.bucket
        self._api = self._client.write_api()

    async def close(self):
        await self._client.close()

    async def write(self, haus: Haus, fields: Dict[str, float]):
        # version = await self._client.version()
        # logger.info(f"InfluxDB: {version}")

        dict_tags = {
            "position": haus.grafana_tag,  # "haus_08", "zentral"
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
        fields: List[str:str] = {}
        for i, tag in (
            (1, "sp_oben"),
            (2, "sp_mitte"),
            (3, "sp_unten"),
        ):
            pair_ds18 = modbus_iregs_all.pairs_ds18[i]
            fields[f"{tag}_temperature_C"] = pair_ds18.temperature_C
            fields[f"{tag}_error_C"] = pair_ds18.error_C
        await self.write(haus=haus, fields=fields)


async def main():
    secrets = InfluxSecrets("Puenterswis")

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
