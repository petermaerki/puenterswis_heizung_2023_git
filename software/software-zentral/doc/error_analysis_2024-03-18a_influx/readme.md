```
2024-03-17 22:31:58,275 util_modbus_haus.py:81 - ERROR - Haus 7(modbus=107): ModbusIOException('[Input/Output] ERROR: No response received after 0 retries')
2024-03-17 22:39:37,408 util_modbus.py:38 - WARNING - MyAsyncModbusSerialClient: close(reconnect=True)
2024-03-17 22:39:37,408 util_modbus_haus.py:81 - ERROR - Haus 8(modbus=108): ModbusIOException('[Input/Output] ERROR: No response received after 0 retries')
2024-03-17 22:54:54,026 util_modbus.py:38 - WARNING - MyAsyncModbusSerialClient: close(reconnect=True)
2024-03-17 22:54:54,028 util_modbus_haus.py:81 - ERROR - Haus 5(modbus=105): ModbusIOException('[Input/Output] ERROR: No response received after 0 retries')
2024-03-17 22:55:21,024 util_modbus.py:38 - WARNING - MyAsyncModbusSerialClient: close(reconnect=True)
2024-03-17 22:55:21,026 util_modbus_haus.py:81 - ERROR - Haus 13(modbus=113): ModbusIOException('[Input/Output] ERROR: No response received after 0 retries')
2024-03-17 23:04:07,700 util_modbus.py:38 - WARNING - MyAsyncModbusSerialClient: close(reconnect=True)
2024-03-17 23:04:07,702 util_modbus_haus.py:81 - ERROR - Haus 17(modbus=117): ModbusIOException('[Input/Output] ERROR: No response received after 0 retries')
2024-03-17 23:09:26,827 util_modbus.py:38 - WARNING - MyAsyncModbusSerialClient: close(reconnect=True)
2024-03-17 23:09:26,827 util_modbus_haus.py:81 - ERROR - Haus 24(modbus=124): ModbusIOException('[Input/Output] ERROR: No response received after 0 retries')
2024-03-17 23:12:32,627 runners.py:118 - ERROR - Task exception was never retrieved
future: <Task finished name='Task-4' coro=<ModbusCommunication.task_modbus() done, defined at /home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/util_modbus_communication.py:62> exception=TimeoutError()>
Traceback (most recent call last):
  File "/home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/util_modbus_communication.py", line 64, in task_modbus
    await self.modbus_haueser_loop()
  File "/home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/util_modbus_communication.py", line 58, in modbus_haueser_loop
    await self._context.influx.write_records(records=r)
  File "/home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/util_influx.py", line 57, in write_records
    success = await self._api.write(bucket=self._bucket, record=records._records)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/client/write_api_async.py", line 121, in write
    response = await self._write_service.post_write_async(org=org, bucket=bucket, body=body,
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/service/write_service.py", line 131, in post_write_async
    return await self.api_client.call_api(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/_async/api_client.py", line 173, in __call_api
    response_data = await self.request(
                    ^^^^^^^^^^^^^^^^^^^
  File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/_async/rest.py", line 280, in POST
    return (await self.request("POST", url,
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/_async/rest.py", line 225, in request
    r = await self.pool_manager.request(**args)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/client.py", line 605, in _request
    await resp.start(conn)
  File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/client_reqrep.py", line 961, in start
    with self._timer:
  File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/helpers.py", line 735, in __exit__
    raise asyncio.TimeoutError from None
TimeoutError
2024-03-17 23:12:33,627 runners.py:118 - ERROR - Task exception was never retrieved
future: <Task finished name='Task-5' coro=<Context.task_hsm() done, defined at /home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/context.py:44> exception=TimeoutError()>
Traceback (most recent call last):
  File "/home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/context.py", line 48, in task_hsm
    await self.influx.send_hsm_dezental(
  File "/home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/util_influx.py", line 120, in send_hsm_dezental
    await self.write_records(records=r)
  File "/home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/util_influx.py", line 57, in write_records
    success = await self._api.write(bucket=self._bucket, record=records._records)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/client/write_api_async.py", line 121, in write
    response = await self._write_service.post_write_async(org=org, bucket=bucket, body=body,
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/service/write_service.py", line 131, in post_write_async
    return await self.api_client.call_api(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/_async/api_client.py", line 173, in __call_api
    response_data = await self.request(
                    ^^^^^^^^^^^^^^^^^^^
  File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/_async/rest.py", line 280, in POST
    return (await self.request("POST", url,
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/_async/rest.py", line 225, in request
    r = await self.pool_manager.request(**args)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/client.py", line 605, in _request
    await resp.start(conn)
  File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/client_reqrep.py", line 961, in start
    with self._timer:
  File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/helpers.py", line 735, in __exit__
    raise asyncio.TimeoutError from None
TimeoutError

```
