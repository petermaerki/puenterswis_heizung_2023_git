# M-Bus

## Links

 * https://de.wikipedia.org/wiki/M-Bus_(Feldbus)
 * https://m-bus.com/
 * https://www.instructables.com/How-to-Use-the-M-BUS-meter-Bus-to-Read-Smartmeters/

 * Pegelwandler im Heizungraum
   * https://www.relay.de/produkte/m-bus-master/masterfamilien-w60

 * Implementierungen ausgeählt
    * https://pypi.org/project/pyMeterBus/
     * https://github.com/ganehag/pyMeterBus

 * Implementierungen
   * https://github.com/rscada/libmbus
   * https://github.com/bsdphk/PyKamstrup
   * https://esphome.io/components/sensor/kamstrup_kmp.html
     * https://github.com/esphome/esphome/blob/dev/esphome/components/kamstrup_kmp/sensor.py
   * https://github.com/gertvdijk/PyKMP
     * https://gertvdijk.github.io/PyKMP/

 * Zähler Peter
   * https://www.photovoltaikforum.com/core/attachment/283797-sharky-775-kommunikationsbeschreibung-pdf/
   * 31892743  1E6A507

 * Dokumentation neuer Zähler
   * Wärmezähler (E1)
   * Kältezähler (E3)
   * Klasse: 2 (E1, M2)
   * Typ: 303TA03CA
   * A/N: 20648200
   * S/N: 82969010/H7/24
   * https://www.kamstrup.com/en-en/heat-solutions/meters-devices/meters/multical-303/documents
     * FILE100001554_C_EN-55122701_F1pdf.pdf


## Documenation

* Type number
  ```
  303TA03CA
     ^      Sensor: Pt500 heat/cooling meter
      ^^    Flow Sensor: 2.5 m3/h
        ^   Heat/cooling meter PHIhc=off
         ^^ Country Code
  ```

  ```
  303-xxxxxx-xxxxx
  ^^^ ^^^^^^  Factory set
             ^^^^^ not written (?)

  Serial Number
  xxxxxxxx/WW/yy
  82969010/H7/24
  ^^^^^^^^       Serial number
           ^^    Device code, Extended availability paragraph 3.4
              ^^ Production year

  Config number: Is not writte on the meter, but can be ...
  ```
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

2024-09-10
```bash
time mbus-serial-scan-primary -b 2400 /dev/ttyACM2
Found a M-Bus device at address 10
Found a M-Bus device at address 11
Found a M-Bus device at address 12
Found a M-Bus device at address 15
Found a M-Bus device at address 16
Found a M-Bus device at address 17
Found a M-Bus device at address 75
Nach 16 min abgebrochen

time mbus-serial-scan-primary -b 2400 -r 0 /dev/ttyACM2
5min

time mbus-serial-scan-secondary -b 2400 -r 0 --address FFFFFFFFFFFFFFFF /dev/ttyACM2
4min

mbus-serial-req-single -b 2400 -a 12 -d /dev/ttyACM2
meterbus.exceptions.MBusFrameDecodeError: ('empty frame', None)
```

2024-09-10: Zähler Peter abgetrennt (11 is weg)
```bash
time mbus-serial-scan-primary -b 2400 -r 0 /dev/ttyACM2
Found a M-Bus device at address 10
Found a M-Bus device at address 12
Found a M-Bus device at address 15
Found a M-Bus device at address 17
Found a M-Bus device at address 74
Found a M-Bus device at address 77
```

2024-09-10: Weiter Zähler installiert (neu sind 76 und 79)
```bash
Found a M-Bus device at address 10
Found a M-Bus device at address 12
Found a M-Bus device at address 15
Found a M-Bus device at address 17
Found a M-Bus device at address 74
Found a M-Bus device at address 76
Found a M-Bus device at address 79
```

2024-09-10: Weiter Zähler installiert. Zähler Peter angeschlossen. (keine Veränderung)
```bash
Found a M-Bus device at address 10
Found a M-Bus device at address 12
Found a M-Bus device at address 15
Found a M-Bus device at address 17
Found a M-Bus device at address 74
Found a M-Bus device at address 76
Found a M-Bus device at address 79
```

## Primary/Secondary address

```bash
time mbus-serial-scan-primary -b 2400 -r 0 -d /dev/ttyACM2
INFO:meterbus.serial:SEND (005) 10 40 09 49 16
INFO:meterbus.serial:SEND (005) 10 40 0A 4A 16
INFO:meterbus.serial:RECV (001) E5
Found a M-Bus device at address 10
INFO:meterbus.serial:SEND (005) 10 40 0B 4B 16
INFO:meterbus.serial:SEND (005) 10 40 0C 4C 16
INFO:meterbus.serial:RECV (001) E5
Found a M-Bus device at address 12
INFO:meterbus.serial:SEND (005) 10 40 0D 4D 16
INFO:meterbus.serial:SEND (005) 10 40 0E 4E 16
INFO:meterbus.serial:SEND (005) 10 40 0F 4F 16
INFO:meterbus.serial:RECV (001) E5
Found a M-Bus device at address 15
```

Concusion
```
10 40 0A 4A 16
      ^^       Primary address is 10
```

```bash
mbus-serial-scan-secondary -d -b 2400 --address FFFFFFFFFFFFFFFF /dev/ttyACM2

INFO:meterbus.serial:SEND (005) 10 40 FD 3D 16
INFO:meterbus.serial:SEND (005) 10 40 FF 3F 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF FF 0F FF FF FF FF CA 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF FF 1F FF FF FF FF DA 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF FF 2F FF FF FF FF EA 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF FF 3F FF FF FF FF FA 16
                                                              ^ Mask
INFO:meterbus.serial:RECV (001) 00
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF FF 30 FF FF FF FF EB 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF FF 31 FF FF FF FF EC 16
                                                              ^^ Address found
INFO:meterbus.serial:RECV (001) 00
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 0F 31 FF FF FF FF FC 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 1F 31 FF FF FF FF 0C 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 2F 31 FF FF FF FF 1C 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 3F 31 FF FF FF FF 2C 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 4F 31 FF FF FF FF 3C 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 5F 31 FF FF FF FF 4C 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 6F 31 FF FF FF FF 5C 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 7F 31 FF FF FF FF 6C 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 8F 31 FF FF FF FF 7C 16
                                                           ^ Mask
INFO:meterbus.serial:RECV (001) 00
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 80 31 FF FF FF FF 6D 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 81 31 FF FF FF FF 6E 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 82 31 FF FF FF FF 6F 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 83 31 FF FF FF FF 70 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 84 31 FF FF FF FF 71 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 85 31 FF FF FF FF 72 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 86 31 FF FF FF FF 73 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 87 31 FF FF FF FF 74 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 88 31 FF FF FF FF 75 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF FF 89 31 FF FF FF FF 76 16
                                                           ^^ ^^ Address found
INFO:meterbus.serial:RECV (001) 00
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF 0F 89 31 FF FF FF FF 86 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF 1F 89 31 FF FF FF FF 96 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF 2F 89 31 FF FF FF FF A6 16
                                                        ^ Mask
INFO:meterbus.serial:RECV (001) 00
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF 20 89 31 FF FF FF FF 97 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF 21 89 31 FF FF FF FF 98 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF 22 89 31 FF FF FF FF 99 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF 23 89 31 FF FF FF FF 9A 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF 24 89 31 FF FF FF FF 9B 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF 25 89 31 FF FF FF FF 9C 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF 26 89 31 FF FF FF FF 9D 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 FF 27 89 31 FF FF FF FF 9E 16
                                                        ^^ ^^ ^^ Address found
INFO:meterbus.serial:RECV (001) 00
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 0F 27 89 31 FF FF FF FF AE 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 1F 27 89 31 FF FF FF FF BE 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 2F 27 89 31 FF FF FF FF CE 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 3F 27 89 31 FF FF FF FF DE 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 4F 27 89 31 FF FF FF FF EE 16
                                                     ^ Mask
INFO:meterbus.serial:RECV (001) 00
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 40 27 89 31 FF FF FF FF DF 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 41 27 89 31 FF FF FF FF E0 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 42 27 89 31 FF FF FF FF E1 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 43 27 89 31 FF FF FF FF E2 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 44 27 89 31 FF FF FF FF E3 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 45 27 89 31 FF FF FF FF E4 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 46 27 89 31 FF FF FF FF E5 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 47 27 89 31 FF FF FF FF E6 16
                                                     ^^ ^^ ^^ ^^ Address found
INFO:meterbus.serial:RECV (001) E5
   Address confirmend
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 48 27 89 31 FF FF FF FF E7 16
INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 49 27 89 31 FF FF FF FF E8 16
                                                     ^^ ^^ ^^ ^^ Address found
INFO:meterbus.serial:RECV (001) E5
   Address confirmend
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16

https://m-bus.com/documentation-wired/07-network-layer
68 0B 0B 68 73 FD 52 49 27 89 31 FF FF FF FF E8 16
               ^^ ^^ address FDh and the control information 52h / 56h are the indication for the slaves
                     to compare the following secondary addresses with their own, and to change into the
                     selected state should they agree
                     ^^ ^^ ^^ ^^ identification number
                                 ^^ ^^ manufacturer
                                       ^^ version
                                          ^^ medium


INFO:meterbus.serial:SEND (017) 68 0B 0B 68 73 FD 52 47 27 89 31 FF FF FF FF E6 16
INFO:meterbus.serial:RECV (001) E5
INFO:meterbus.serial:SEND (005) 10 5B FD 58 16
INFO:meterbus.serial:RECV (001) 68
INFO:meterbus.serial:RECV (001) 5E
INFO:meterbus.serial:RECV (001) 5E
INFO:meterbus.serial:RECV (001) 68
INFO:meterbus.serial:RECV (001) 08
INFO:meterbus.serial:RECV (001) 00
INFO:meterbus.serial:RECV (001) 72
INFO:meterbus.serial:RECV (001) 47
INFO:meterbus.serial:RECV (001) 27
INFO:meterbus.serial:RECV (091) 89 31 24 23 28 04 ED 00 00 00 0C 05 31 84 74 01 0C 12 91 72 64 02 0C 2A 00 00 00 00 0B 3A 00 00 00 0A 5A 22 05 0A 5E 23 04 0A 62 99 00 04 6D 21 16 0A 39 4C 05 30 78 11 00 44 6D 00 00 1E 14 44 ED 7E 00 00 3F 1C 8C 01 05 20 30 69 01 84 01 6D 00 00 FF 2C 0B 26 02 03 16 F5 16
Device found with id 3189274724232804 (HYD), using mask 31892747FFFFFFFF



Device found with id 3189274724232804 (HYD), using mask 31892747FFFFFFFF
Device found with id 3189274924232804 (HYD), using mask 31892749FFFFFFFF
Device found with id 829690102D2C400D (KAM), using mask 82969010FFFFFFFF
Device found with id 829690122D2C400D (KAM), using mask 82969012FFFFFFFF
Device found with id 829690152D2C400D (KAM), using mask 82969015FFFFFFFF
Device found with id 829690172D2C400D (KAM), using mask 82969017FFFFFFFF
Device found with id 830036742D2C400D (KAM), using mask 83003674FFFFFFFF
Device found with id 830036752D2C400D (KAM), using mask 83003675FFFFFFFF
Device found with id 830036762D2C400D (KAM), using mask 83003676FFFFFFFF
Device found with id 830036772D2C400D (KAM), using mask 83003677FFFFFFFF
Device found with id 830036792D2C400D (KAM), using mask 83003679FFFFFFFF
       
Blink: 11, 16
                     8FFFFFFFFFFFFFFF

   * S/N: 82969010/H7/24 = 0x4F201B2
 
