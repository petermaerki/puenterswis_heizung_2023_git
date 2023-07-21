# Installation SDCARD

https://www.raspberrypi.com/software/
https://www.raspberrypi.com/software/operating-systems/
Raspberry Pi OS Lite
Release date: May 3rd 2023
System: 32-bit
Kernel version: 6.1
Debian version: 11 (bullseye)
Size: 364MB

## Konfiguration von "Raspberry Pi Imager"

* Ort: puent / bochs
* Hostname: puentpi / bochspi
* Enable SSH
  * Allow public-key authentication only
  * authorized_keys for 'pi': <empty>
* User: pi / guguseli
* WLAN: u / guguseli
* Set locale settings: Europe/Zurich - us

## Diverses

USB Power neben Befestigungsloch

## Mount SSH FS

VSCode: Add extension SSH FS extension `Kelvin.vscode-sshfs`
VSCode, SSH FS extension: ..

## Initial creation of ssh keys

* `INITIAL_10_KEYGEN`
```
cd keys
./do_10_ssh-keygen.sh
```

* `INITIAL_20_KEYDEPLOY`
Copy keys/zero-*/id_rsa.pub to autorized_keys on www.maerki.com

## Copy ssh keys

* `INITIAL_30_CREATEIMG`
cp keys/zero-bochspi <bochspi>/home/pi/.ssh
cp keys/zero-bochspi <bochspi>/home/pi/.ssh

cd <bochspi>/home/pi/.ssh
chmod u=rw,go= id_rsa
chmod u=rw,go=r id_rsa.pub authorized_keys
