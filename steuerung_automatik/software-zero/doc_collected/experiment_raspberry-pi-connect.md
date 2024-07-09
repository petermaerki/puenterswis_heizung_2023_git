# Raspberry Pi connect

* https://www.raspberrypi.com/news/raspberry-pi-connect/

* https://www.raspberrypi.com/documentation/computers/remote-access.html#raspberry-pi-connect

* https://www.raspberrypi.com/documentation/services/connect.html

```bash
time (sudo apt update && sudo apt upgrade && sudo apt install rpi-connect-lite && sudo apt autoremove -y)
sudo reboot
loginctl enable-linger
```


    systemctl --user start rpi-connect.service

For information on getting started with Raspberry Pi Connect, please see the official documentation:

    https://rptl.io/rpi-connect



rpi-connect signin


## Conclusion

* How to store/restore the credential when a device has been replaced?
* How to connect a device to two accounts?
* RPI-Connect does NOT seem to support ssh from the command line
