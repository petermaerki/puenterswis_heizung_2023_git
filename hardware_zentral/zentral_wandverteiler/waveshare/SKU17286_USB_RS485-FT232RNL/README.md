https://www.waveshare.com/usb-to-rs485.htm

https://www.waveshare.com/wiki/USB_TO_RS485

Original FT232RNL and SP485EEN chip.


```
dmesg --follow
[ 5320.729865] usb 1-2.2.4: new full-speed USB device number 14 using xhci_hcd
[ 5320.843714] usb 1-2.2.4: New USB device found, idVendor=0403, idProduct=6001, bcdDevice= 6.00
[ 5320.843719] usb 1-2.2.4: New USB device strings: Mfr=1, Product=2, SerialNumber=3
[ 5320.843721] usb 1-2.2.4: Product: FT232R USB UART
[ 5320.843722] usb 1-2.2.4: Manufacturer: FTDI
[ 5320.843724] usb 1-2.2.4: SerialNumber: B001K4G7
[ 5320.852792] ftdi_sio 1-2.2.4:1.0: FTDI USB Serial Device converter detected
[ 5320.852834] usb 1-2.2.4: Detected FT232R
[ 5320.853331] usb 1-2.2.4: FTDI USB Serial Device converter now attached to ttyUSB0

lsusb
Bus 001 Device 014: ID 0403:6001 Future Technology Devices International, Ltd FT232 Serial (UART) IC

ls /dev/ttyUSB0
```