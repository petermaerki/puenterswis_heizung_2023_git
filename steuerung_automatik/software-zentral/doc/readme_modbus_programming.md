## Requirements for the use of Modbus

### Modbus calls in two asyncio tasks must not interleave

### Correct sleep after modbus call (success & fail)

### Failing Modbus calls: Must not terminate task

### Failing Modbus calls: Must still update the application state

### Real Modbus errors (usb not connected): Must terminate the application

### Ability to log Modbus calls in debug file

### Grafana: events should be queued

## Current implementation

Pattern:

```python
        try:
            rsp = await self._modbus.read_input_registers(
                slave=haus.config_haus.modbus_server_id,
                address=EnumModbusRegisters.SETGET16BIT_ALL_SLOW,
                count=IREGS_ALL.register_count,
            )
        except ConnectionException as exc:
            logger.error(f"{haus.label}: {exc!r}")
            os._exit(42)
        except ModbusException as exc:
            logger.error(f"{haus.label}: {exc!r}")
            haus.status_haus.hsm_dezentral.dispatch(hsm_dezentral_signal.SignalModbusFailed())
            await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
            return False
```
