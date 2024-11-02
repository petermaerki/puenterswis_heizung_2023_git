import asyncio
import logging

from zentral.config_secrets import InfluxSecrets
from zentral.util_influx import Influx
from influxdb_client import QueryApi  # type: ignore[import]
from influxdb_client.client.influxdb_client import InfluxDBClient  # type: ignore[import]

logger = logging.getLogger(__name__)

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

def main():
    secrets = InfluxSecrets()
    read_token = "xxxx"
    client = InfluxDBClient(url=secrets.url, token=read_token, org=secrets.org)
    query_api = client.query_api()

    query = f"""from(bucket: "{secrets.bucket}")
    |> range(start: -100m)
    |> filter(fn: (r) => r._field == "mbus_dezentral_energy_heating_E1_Wh" 
    or r._field == "mbus_dezentral_energy_cooling_E3_Wh"
    or r._field == "mbus_sum_energy_E1_minus_E3_Wh"
    or r._field == "mischventil_energy_Wh"
    ) """
    tables = query_api.query(query)

    for table in tables:
        for record in table.records:
            # print(record)
            print("---")
            for key in ("_field", "etappe", "position", "_time", "_value"):
                print(f"  {key}: {record.values[key]}")


if __name__ == "__main__":
    main()
