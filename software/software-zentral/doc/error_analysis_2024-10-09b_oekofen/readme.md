## TODO: Puent 10:47 brenner 2 -100%

2024-10-09 10:44:22,986 INFO handler_sp_zentral.py:29 ladung_aufwaerts = True, last_ladung_prozent_auf_ab 53.6
2024-10-09 10:45:26,489 INFO handler_sp_zentral.py:29 ladung_aufwaerts = True, last_ladung_prozent_auf_ab 54.6
2024-10-09 10:46:41,529 WARNING util_modbus_communication.py:281 Oekofen: Modbus Error: Modbus Error: [Input/Output] ERROR: No response received after 0 retries
2024-10-09 10:48:22,528 INFO handler_sp_zentral.py:29 ladung_aufwaerts = True, last_ladung_prozent_auf_ab 55.6
2024-10-09 10:49:07,375 INFO handler_sp_zentral.py:29 ladung_aufwaerts = True, last_ladung_prozent_auf_ab 56.6


## TODO: Bochs 03:10 brenner 2 -100%

2024-10-09 03:08:42,464 INFO handler_last.py:56 update_valves(): valve_open_count=0 target_valve_open_count=2
2024-10-09 03:08:47,058 INFO handler_last.py:56 update_valves(): valve_open_count=0 target_valve_open_count=2
2024-10-09 03:08:51,423 WARNING util_modbus_communication.py:281 Oekofen: Modbus Error: Modbus Error: [Input/Output] ERROR: No response received after 0 retries
2024-10-09 03:08:51,659 INFO handler_last.py:56 update_valves(): valve_open_count=0 target_valve_open_count=2
2024-10-09 03:08:56,110 INFO handler_last.py:56 update_valves(): valve_open_count=0 target_valve_open_count=2

## TODO: Puent 21:00 brenner suction

2024-10-09 20:46:59,034 WARNING connectionpool.py:870 Retrying (WritesRetry(total=999, connect=None, read=None, redirect=None, status=None)) after connection broken by 'ReadTimeoutError("HTTPConnectionPool(host='www.maerki.com', port=8086): Read timed out. (read timeout=9.999273636989528)")': /api/v2/write?org=maerki-org&bucket=heizung&precision=ns
2024-10-09 20:51:18,993 INFO handler_last.py:56 update_valves(): valve_open_count=0 target_valve_open_count=1
2024-10-09 20:51:18,997 INFO handler_last.py:117 _plus_1_valve haus_10
2024-10-09 21:00:15,269 INFO handler_oekofen.py:107 handle_brenner_mit_stoerung(): Brenner 2: brenner_zustand=BrennerZustand(fa_temp_C=77.0, fa_runtime_h=122, verfuegbar=True, zuendet_oder_brennt=False, brennt=False) modulation=MIN->OFF
2024-10-09 21:00:19,028 INFO handler_last.py:56 update_valves(): valve_open_count=1 target_valve_open_count=0
2024-10-09 21:00:19,032 INFO handler_last.py:150 _minus_1_valve haus_10

==> Korrekt. Optimieren

# Versuch Suction, Puent 11:14

Manuell Saugen starten

# Versuch Reinigung/Befüllung, Bochs 11:30

Manuell Reinigung/Befüllung starten
