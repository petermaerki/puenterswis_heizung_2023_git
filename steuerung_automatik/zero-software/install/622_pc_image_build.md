# Installation SDCARD

Goal: Create a SD card which
* automatically connects to the WLAN
* allows access using user/password

## Background: Image

https://www.raspberrypi.com/software/
https://www.raspberrypi.com/software/operating-systems/
Raspberry Pi OS Lite
Release date: May 3rd 2023
System: 32-bit
Kernel version: 6.1
Debian version: 11 (bullseye)
Size: 364MB

## TASK: Create Image

Start: "Raspberry Pi Imager"

Select: Pi OS Lite 32bit
* Hostname: zero-puent / zero-bochs
* Enable SSH
  * Use password authentication
* User: <622_pc_image_build-password.txt>
* WLAN: <622_pc_image_build-password.txt>
* Set locale settings: Europe/Zurich - us
