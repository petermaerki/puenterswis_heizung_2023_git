# M-Bus

## Links

 * https://de.wikipedia.org/wiki/M-Bus_(Feldbus)
 * https://github.com/ganehag/pyMeterBus
 * https://pypi.org/project/pyMeterBus/

 * Zähler Peter
   * https://www.photovoltaikforum.com/core/attachment/283797-sharky-775-kommunikationsbeschreibung-pdf/
   * 31892743  1E6A507

## Python Experiments

Bug:

```bash
serial_arg --pid 55D5 --n "2"
Traceback (most recent call last):
  File "/home/zero/venv_app/bin/serial_arg", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/zero/venv_app/lib/python3.11/site-packages/mp/util_serial_arg.py", line 31, in main
    device = find_serial_port(awf.args)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/zero/venv_app/lib/python3.11/site-packages/mp/util_serial.py", line 90, in find_serial_port
    if n < args.n:
       ^^^^^^^^^^
TypeError: '<' not supported between instances of 'int' and 'str'
```

```bash
$ serial_list 
/dev/ttyACM0
  manufacturer   WCH.CN
  product        USB Quad_Serial
  interface      None
  --vid=1A86 --pid=55D5 --serial=BC045EABCD
/dev/ttyACM1
  manufacturer   WCH.CN
  product        USB Quad_Serial
  interface      None
  --vid=1A86 --pid=55D5 --serial=BC045EABCD
/dev/ttyACM2
  manufacturer   WCH.CN
  product        USB Quad_Serial
  interface      None
  --vid=1A86 --pid=55D5 --serial=BC045EABCD
/dev/ttyACM3
  manufacturer   WCH.CN
  product        USB Quad_Serial
  interface      None
  --vid=1A86 --pid=55D5 --serial=BC045EABCD

# 0x55D5
#   zentral/util_modbus_communication.py: 
#     self._modbus = ModbusWrapper(...n=0... -> /dev/ttyACM0
#     self._modbus_oekofen = ModbusWrapper(...n=1.. ->/dev/ttyACM1

pip install pyMeterBus

mbus-serial-scan-primary
usage: mbus-serial-scan-primary [-h] [-d] [-b BAUDRATE] [-r RETRIES] [--echofix] device

mbus-serial-scan-primary -d -b 2400 /dev/ttyACM2
mbus-serial-scan-secondary -d -b 2400 --address FFFFFFFFFFFFFFFF /dev/ttyACM2

INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 40 27 89 31 FF FF FF FF DF 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 41 27 89 31 FF FF FF FF E0 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 42 27 89 31 FF FF FF FF E1 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 43 27 89 31 FF FF FF FF E2 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 44 27 89 31 FF FF FF FF E3 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 45 27 89 31 FF FF FF FF E4 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 46 27 89 31 FF FF FF FF E5 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 47 27 89 31 FF FF FF FF E6 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 48 27 89 31 FF FF FF FF E7 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 49 27 89 31 FF FF FF FF E8 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 5F 27 89 31 FF FF FF FF FE 16
INFO:meterbus.serial:RECV (001) 00
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 50 27 89 31 FF FF FF FF EF 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 51 27 89 31 FF FF FF FF F0 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 52 27 89 31 FF FF FF FF F1 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 53 27 89 31 FF FF FF FF F2 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 54 27 89 31 FF FF FF FF F3 16
INFO:meterbus.serial:RECV (001) E5

INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 54 27 89 31 FF FF FF FF F3 16
                                   ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff 

mbus-serial-req-single --help
usage: mbus-serial-req-single [-h] [-d] [-b BAUDRATE] [-a ADDRESS] [-r RETRIES] [-o OUTPUT] [--echofix] device

Request data over serial M-Bus for devices.

positional arguments:
  device                Serial device, URI or binary file

options:
  -h, --help            show this help message and exit
  -d                    Enable verbose debug
  -b BAUDRATE, --baudrate BAUDRATE
                        Serial bus baudrate
  -a ADDRESS, --address ADDRESS
                        Primary or secondary address
  -r RETRIES, --retries RETRIES
                        Number of ping retries for each address
  -o OUTPUT, --output OUTPUT
                        Output format
  --echofix             Read and ignore echoed data from target

mbus-serial-req-single -d -b 2400 --address 0B0B6873FD5254278931FFFFFFFFF316 /dev/ttyACM2
   -> Kein Output
```

```python
```
