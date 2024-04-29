import asyncio
from zentral.util_influx import Influx


async def main():
    influx = Influx()
    await influx.delete_bucket_virgin()
    await influx.close_and_flush()


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
