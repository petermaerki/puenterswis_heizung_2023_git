https://www.waveshare.com/usb-to-4ch-rs485.htm

https://www.waveshare.com/wiki/USB_TO_4CH_RS485

USB TO 4CH RS485

```
dmesg --follow
[ 9157.412088] usb 1-2.2.3: new full-speed USB device number 19 using xhci_hcd
[ 9157.527662] usb 1-2.2.3: New USB device found, idVendor=1a86, idProduct=55d5, bcdDevice= 1.48
[ 9157.527667] usb 1-2.2.3: New USB device strings: Mfr=1, Product=2, SerialNumber=3
[ 9157.527669] usb 1-2.2.3: Product: USB Quad_Serial
[ 9157.527686] usb 1-2.2.3: Manufacturer: WCH.CN
[ 9157.527688] usb 1-2.2.3: SerialNumber: BC045EABCD
[ 9157.561237] cdc_acm 1-2.2.3:1.0: ttyACM1: USB ACM device
[ 9157.561514] cdc_acm 1-2.2.3:1.2: ttyACM2: USB ACM device
[ 9157.561775] cdc_acm 1-2.2.3:1.4: ttyACM3: USB ACM device
[ 9157.562056] cdc_acm 1-2.2.3:1.6: ttyACM4: USB ACM device

lsusb
Bus 001 Device 019: ID 1a86:55d5 QinHeng Electronics USB Quad_Serial

ls /dev/ttyACM*
/dev/ttyACM0
/dev/ttyACM1
/dev/ttyACM2
/dev/ttyACM3
```