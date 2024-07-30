```python
Mar 17 07:55:59 zero-puent systemd[1]: Stopping heizung-app.service - Heizung app...
Mar 17 07:56:00 zero-puent bash[16382]: INFO:     Shutting down
Mar 17 07:56:00 zero-puent bash[16382]: INFO:     Waiting for application shutdown.
Mar 17 07:56:00 zero-puent bash[16382]: util_modbus.py:38 - WARNING - MyAsyncModbusSerialClient: close(reconnect=False)
Mar 17 07:56:00 zero-puent bash[16382]: ERROR:    Traceback (most recent call last):
Mar 17 07:56:00 zero-puent bash[16382]:   File "/home/zero/.local/lib/python3.11/site-packages/starlette/routing.py", line 734, in lifespan
Mar 17 07:56:00 zero-puent bash[16382]:     async with self.lifespan_context(app) as maybe_state:
Mar 17 07:56:00 zero-puent bash[16382]:   File "/usr/lib/python3.11/contextlib.py", line 211, in __aexit__
Mar 17 07:56:00 zero-puent bash[16382]:     await anext(self.gen)
Mar 17 07:56:00 zero-puent bash[16382]:   File "/home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/run_zentral>
Mar 17 07:56:00 zero-puent bash[16382]:     async with cls_ctx(config_bochs.create_config_bochs()) as ctx:
Mar 17 07:56:00 zero-puent bash[16382]:   File "/home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/context.py">
Mar 17 07:56:00 zero-puent bash[16382]:     await self.modbus_communication.close()
Mar 17 07:56:00 zero-puent bash[16382]:   File "/home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/util_modbus>
Mar 17 07:56:00 zero-puent bash[16382]:     await self._modbus.close()
Mar 17 07:56:00 zero-puent bash[16382]:   File "/home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/util_modbus>
Mar 17 07:56:00 zero-puent bash[16382]:     await self._modbus_client.close()
Mar 17 07:56:00 zero-puent bash[16382]: TypeError: object NoneType can't be used in 'await' expression
Mar 17 07:56:00 zero-puent bash[16382]: ERROR:    Application shutdown failed. Exiting.
Mar 17 07:56:00 zero-puent bash[16382]: INFO:     Finished server process [16382]
Mar 17 07:56:00 zero-puent bash[16382]: client.py:367 - ERROR - Unclosed client session
Mar 17 07:56:00 zero-puent bash[16382]: client_session: <aiohttp.client.ClientSession object at 0x7f84b1fa90>
Mar 17 07:56:00 zero-puent bash[16382]: connector.py:285 - ERROR - Unclosed connector
Mar 17 07:56:00 zero-puent bash[16382]: connections: ['[(<aiohttp.client_proto.ResponseHandler object at 0x7f84976a50>, 55290.796), (<aiohttp.cl>
Mar 17 07:56:00 zero-puent bash[16382]: connector: <aiohttp.connector.TCPConnector object at 0x7f849478d0>
```

```python
Mar 15 22:59:13 zero-puent python[725]: aiohttp.client_exceptions.ClientConnectorError: Cannot connect to host www.maerki.com:8086 ssl:default [Temporary failure in name resolution]
Mar 15 22:59:13 zero-puent python[725]: ERROR:zentral.util_modbus_haus:Haus 9(modbus=109): ModbusIOException('[Input/Output] ERROR: No response received after 1 retries')
Mar 15 22:59:13 zero-puent python[725]: util_modbus_haus.py:81 - ERROR - Haus 9(modbus=109): ModbusIOException('[Input/Output] ERROR: No response received after 1 retries')
Mar 15 22:59:13 zero-puent python[725]: ERROR:zentral.util_influx:Failed to write to influx
Mar 15 22:59:13 zero-puent python[725]: Traceback (most recent call last):
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/connector.py", line 1173, in _create_direct_connection
Mar 15 22:59:13 zero-puent python[725]:     hosts = await asyncio.shield(host_resolved)
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/connector.py", line 884, in _resolve_host
Mar 15 22:59:13 zero-puent python[725]:     addrs = await self._resolver.resolve(host, port, family=self._family)
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/resolver.py", line 33, in resolve
Mar 15 22:59:13 zero-puent python[725]:     infos = await self._loop.getaddrinfo(
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/usr/lib/python3.11/asyncio/base_events.py", line 867, in getaddrinfo
Mar 15 22:59:13 zero-puent python[725]:     return await self.run_in_executor(
Mar 15 22:59:13 zero-puent python[725]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/usr/lib/python3.11/concurrent/futures/thread.py", line 58, in run
Mar 15 22:59:13 zero-puent python[725]:     result = self.fn(*self.args, **self.kwargs)
Mar 15 22:59:13 zero-puent python[725]:              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/usr/lib/python3.11/socket.py", line 962, in getaddrinfo
Mar 15 22:59:13 zero-puent python[725]:     for res in _socket.getaddrinfo(host, port, family, type, proto, flags):
Mar 15 22:59:13 zero-puent python[725]:                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]: socket.gaierror: [Errno -3] Temporary failure in name resolution
Mar 15 22:59:13 zero-puent python[725]: The above exception was the direct cause of the following exception:
Mar 15 22:59:13 zero-puent python[725]: Traceback (most recent call last):
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/util_influx.py", line 57, in write_records
Mar 15 22:59:13 zero-puent python[725]:     success = await self._api.write(bucket=self._bucket, record=records._records)
Mar 15 22:59:13 zero-puent python[725]:               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/client/write_api_async.py", line 121, in write
Mar 15 22:59:13 zero-puent python[725]:     response = await self._write_service.post_write_async(org=org, bucket=bucket, body=body,
Mar 15 22:59:13 zero-puent python[725]:                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/service/write_service.py", line 131, in post_write_async
Mar 15 22:59:13 zero-puent python[725]:     return await self.api_client.call_api(
Mar 15 22:59:13 zero-puent python[725]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/_async/api_client.py", line 173, in __call_api
Mar 15 22:59:13 zero-puent python[725]:     response_data = await self.request(
Mar 15 22:59:13 zero-puent python[725]:                     ^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/_async/rest.py", line 280, in POST
Mar 15 22:59:13 zero-puent python[725]:     return (await self.request("POST", url,
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/_async/rest.py", line 225, in request
Mar 15 22:59:13 zero-puent python[725]:     r = await self.pool_manager.request(**args)
Mar 15 22:59:13 zero-puent python[725]:         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/client.py", line 578, in _request
Mar 15 22:59:13 zero-puent python[725]:     conn = await self._connector.connect(
Mar 15 22:59:13 zero-puent python[725]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/connector.py", line 544, in connect
Mar 15 22:59:13 zero-puent python[725]:     proto = await self._create_connection(req, traces, timeout)
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/connector.py", line 911, in _create_connection
Mar 15 22:59:13 zero-puent python[725]:     _, proto = await self._create_direct_connection(req, traces, timeout)
Mar 15 22:59:13 zero-puent python[725]:                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/connector.py", line 1187, in _create_direct_connection
Mar 15 22:59:13 zero-puent python[725]:     raise ClientConnectorError(req.connection_key, exc) from exc
Mar 15 22:59:13 zero-puent python[725]: aiohttp.client_exceptions.ClientConnectorError: Cannot connect to host www.maerki.com:8086 ssl:default [Temporary failure in name resolution]
Mar 15 22:59:13 zero-puent python[725]: util_influx.py:61 - ERROR - Failed to write to influx
Mar 15 22:59:13 zero-puent python[725]: Traceback (most recent call last):
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/connector.py", line 1173, in _create_direct_connection
Mar 15 22:59:13 zero-puent python[725]:     hosts = await asyncio.shield(host_resolved)
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/connector.py", line 884, in _resolve_host
Mar 15 22:59:13 zero-puent python[725]:     addrs = await self._resolver.resolve(host, port, family=self._family)
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/resolver.py", line 33, in resolve
Mar 15 22:59:13 zero-puent python[725]:     infos = await self._loop.getaddrinfo(
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/usr/lib/python3.11/asyncio/base_events.py", line 867, in getaddrinfo
Mar 15 22:59:13 zero-puent python[725]:     return await self.run_in_executor(
Mar 15 22:59:13 zero-puent python[725]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/usr/lib/python3.11/concurrent/futures/thread.py", line 58, in run
Mar 15 22:59:13 zero-puent python[725]:     result = self.fn(*self.args, **self.kwargs)
Mar 15 22:59:13 zero-puent python[725]:              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/usr/lib/python3.11/socket.py", line 962, in getaddrinfo
Mar 15 22:59:13 zero-puent python[725]:     for res in _socket.getaddrinfo(host, port, family, type, proto, flags):
Mar 15 22:59:13 zero-puent python[725]:                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]: socket.gaierror: [Errno -3] Temporary failure in name resolution
Mar 15 22:59:13 zero-puent python[725]: The above exception was the direct cause of the following exception:
Mar 15 22:59:13 zero-puent python[725]: Traceback (most recent call last):
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/puenterswis_heizung_2023_git/software/software-zentral/zentral/util_influx.py", line 57, in write_records
Mar 15 22:59:13 zero-puent python[725]:     success = await self._api.write(bucket=self._bucket, record=records._records)
Mar 15 22:59:13 zero-puent python[725]:               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/client/write_api_async.py", line 121, in write
Mar 15 22:59:13 zero-puent python[725]:     response = await self._write_service.post_write_async(org=org, bucket=bucket, body=body,
Mar 15 22:59:13 zero-puent python[725]:                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/service/write_service.py", line 131, in post_write_async
Mar 15 22:59:13 zero-puent python[725]:     return await self.api_client.call_api(
Mar 15 22:59:13 zero-puent python[725]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/_async/api_client.py", line 173, in __call_api
Mar 15 22:59:13 zero-puent python[725]:     response_data = await self.request(
Mar 15 22:59:13 zero-puent python[725]:                     ^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/_async/rest.py", line 280, in POST
Mar 15 22:59:13 zero-puent python[725]:     return (await self.request("POST", url,
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/influxdb_client/_async/rest.py", line 225, in request
Mar 15 22:59:13 zero-puent python[725]:     r = await self.pool_manager.request(**args)
Mar 15 22:59:13 zero-puent python[725]:         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/client.py", line 578, in _request
Mar 15 22:59:13 zero-puent python[725]:     conn = await self._connector.connect(
Mar 15 22:59:13 zero-puent python[725]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/connector.py", line 544, in connect
Mar 15 22:59:13 zero-puent python[725]:     proto = await self._create_connection(req, traces, timeout)
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/connector.py", line 911, in _create_connection
Mar 15 22:59:13 zero-puent python[725]:     _, proto = await self._create_direct_connection(req, traces, timeout)
Mar 15 22:59:13 zero-puent python[725]:                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/connector.py", line 1187, in _create_direct_connection
Mar 15 22:59:13 zero-puent python[725]:     raise ClientConnectorError(req.connection_key, exc) from exc
Mar 15 22:59:13 zero-puent python[725]: aiohttp.client_exceptions.ClientConnectorError: Cannot connect to host www.maerki.com:8086 ssl:default [Temporary failure in name resolution]
Mar 15 22:59:13 zero-puent python[725]: ERROR:zentral.util_influx:Failed to write to influx
Mar 15 22:59:13 zero-puent python[725]: Traceback (most recent call last):
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/connector.py", line 1173, in _create_direct_connection
Mar 15 22:59:13 zero-puent python[725]:     hosts = await asyncio.shield(host_resolved)
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/connector.py", line 884, in _resolve_host
Mar 15 22:59:13 zero-puent python[725]:     addrs = await self._resolver.resolve(host, port, family=self._family)
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/home/zero/.local/lib/python3.11/site-packages/aiohttp/resolver.py", line 33, in resolve
Mar 15 22:59:13 zero-puent python[725]:     infos = await self._loop.getaddrinfo(
Mar 15 22:59:13 zero-puent python[725]:             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/usr/lib/python3.11/asyncio/base_events.py", line 867, in getaddrinfo
Mar 15 22:59:13 zero-puent python[725]:     return await self.run_in_executor(
Mar 15 22:59:13 zero-puent python[725]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mar 15 22:59:13 zero-puent python[725]:   File "/usr/lib/python3.11/concurrent/futures/thread.py", line 58, in run
Mar 15 22:59:13 zero-puent python[725]:    ```
