


async def main():
    modbus = get_modbus_client()
    await modbus.connect()

    r = Relais(modbus)
    await r.set(list_relays=(True, True, False, False, False, False, False, False))
    await r.set(list_relays=(False, True, False, False, False, False, False, False))

    await call_belimo(modbus)
    m = Mischventil(modbus=modbus)
    print(f"{await m.absolute_power_kW=}")
    print(f"{await m.zentral_fluss_m3_S=}")
    print(f"{await m.zentral_valve_T1_C=}")
    print(f"{await m.zentral_valve_T2_C=}")
    print(f"{await m.zentral_cooling_energie_J=}")
    print(f"{await m.zentral_heating_energie_J=}")
    print(f"{await m.zentral_cooling_power_W=}")
    print(f"{await m.zentral_heating_power_W=}")
    print(f"{ await m.relative_position=}")
    if False:
        # await relais(modbus)
        # await scan_modbus_slaves(modbus)
        new_setpoint = 0.6 if await m.setpoint < 0.55 else 0.5
        await m.setpoint_set(new_setpoint)
        print(f"{await m.setpoint=}")
        while True:
            relative_position = await m.relative_position
            diff = relative_position - new_setpoint
            print(f"{new_setpoint=:0.2f} {relative_position=:0.2f} {diff=:0.2f}")
            if abs(relative_position - new_setpoint) < 0.01:
                break
            await asyncio.sleep(1.0)

    modbus.close()
    print("Done")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
