# Raspberry Pi Watchdog

Links

* https://raspberrypi.stackexchange.com/questions/108080/watchdog-on-the-rpi4
* https://medium.com/@arslion/enabling-watchdog-on-raspberry-pi-b7e574dcba6b
* man watchdog.conf




## installing

```bash
sudo su
time (sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y)
echo 'dtparam=watchdog=on' >> /boot/firmware/config.txt
sudo apt install watchdog
sudo systemctl status watchdog.service
journalctl --lines 1000 --unit watchdog.service


/etc/systemd/system.conf
```
RuntimeWatchdogSec=15
RebootWatchdogSec=2min


/etc/watchdog.conf
```
watchdog-timeout = 15
max-load-1 = 24
```


## Test with classic forkbomb test

```bash
: (){ :|:& };:
```