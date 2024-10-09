## DONE: puent 23:03: Warum steigt brenner 2 von 30% auf 100%?

2024-10-08 23:03:13,232 INFO controller_master.py:151 _action_in_progress()
2024-10-08 23:03:16,722 INFO util_scenarios.py:82 Scenario: ScenarioOekofenBrennerModulation(brenner_idx0=<BrennerNum.BRENNER_2: 1>, modulation=<Modulation.MAX: 100>): Execute 'action()'
2024-10-08 23:03:16,723 INFO util_modulation_soll.py:260 - brenner idx0=1, 100%(85.0). set_modulation(). Vermutlich Scenario.
2024-10-08 23:03:16,975 INFO util_action.py:32 LastAction-HAUS_PLUS-2.1(5) is_over() -> False

==> Vermutlich Scenario...

## DONE: puent 23:20: brenner 2 modulation soll von 65% -> 0% -> 30%. Warum

2024-10-08 23:20:36,987 INFO controller_master.py:151 _action_in_progress()
2024-10-08 23:20:40,711 INFO util_action.py:32 BrennerAction-LOESCHEN-4.8(20) is_over() -> False
2024-10-08 23:20:40,711 INFO controller_master.py:151 _action_in_progress()
2024-10-08 23:20:41,337 WARNING context.py:42 Received SIGTERM. Cleaning up...
2024-10-08 23:20:41,338 WARNING context.py:44 ...done
2024-10-08 23:20:44,890 INFO hsm_zentral.py:195 controller_master ControllerMasterNone
2024-10-08 23:20:47,110 INFO util_ssh_repl.py:65 Access repl using: ssh -p 8022 localhost
2024-10-08 23:20:48,136 INFO hsm_dezentral.py:181 Haus 1(modbus=101): version sw=0.1.4 hw=1.0.0
2024-10-08 23:20:48,137 INFO util_logger.py:43 HsmHaus01: initializing ==>entry_ok==> ok (modbus_history)

==> Service restart?

## DONE: puent 06:31 Warum fällt brenner 2 soll kurz von 30% auf 0%?

2024-10-09 06:31:41,970 INFO util_action.py:32 PumpeAction-PWM_EIN-13.1(20) is_over() -> False
2024-10-09 06:31:41,971 INFO util_action.py:32 LastAction-HAUS_PLUS-3.2(5) is_over() -> False
2024-10-09 06:31:41,972 INFO controller_master.py:151 _action_in_progress()
2024-10-09 06:31:44,559 WARNING context.py:42 Received SIGTERM. Cleaning up...
2024-10-09 06:31:44,561 WARNING context.py:42 Received SIGTERM. Cleaning up...
2024-10-09 06:31:44,586 WARNING context.py:44 ...done
2024-10-09 06:31:48,082 INFO hsm_zentral.py:195 controller_master ControllerMasterNone

==> Service restart?

## DONE: bochs 03:09 Warum fällt modulation_soll arget_valve_open_count auf -100%

2024-10-09 03:08:38,357 INFO handler_last.py:56 update_valves(): valve_open_count=0 target_valve_open_count=2
2024-10-09 03:08:42,464 INFO handler_last.py:56 update_valves(): valve_open_count=0 target_valve_open_count=2
2024-10-09 03:08:47,058 INFO handler_last.py:56 update_valves(): valve_open_count=0 target_valve_open_count=2
2024-10-09 03:08:51,423 WARNING util_modbus_communication.py:281 Oekofen: Modbus Error: Modbus Error: [Input/Output] ERROR: No response received after 0 retries
2024-10-09 03:08:51,659 INFO handler_last.py:56 update_valves(): valve_open_count=0 target_valve_open_count=2
2024-10-09 03:08:56,110 INFO handler_last.py:56 update_valves(): valve_open_count=0 target_valve_open_count=2
2024-10-09 03:08:59,576 INFO handler_last.py:56 update_valves(): valve_open_count=0 target_valve_open_count=2

==> Fix: enable retires for oekofen

## TODO: bochs 20:13 brenner 2 modulation soll: 30% -> 0%, aber uebersicht prozent reagiert erst 20:16
2024-10-08 20:15:29,296 ERROR util_modbus_exception.py:29 Application wants to terminate. Exit code 42, Task 'modbus', Unexpected SystemExit('No SignalError occured during 62s. Exit the application, the service will restart it.')
2024-10-08 20:15:29,298 ERROR util_modbus_exception.py:30 No SignalError occured during 62s. Exit the application, the service will restart it.


## TODO: Puent 16:08: Benner loescht und füllt Pellets

 30%
-60% 1min
- 3% 8min   SUCTION
- 8% 12min  IGNITION
- 7% 3min   SOFTSTART
 30%