# Installation SDCARD

Goal: Create a SD card, connect via usb-ethernet and configure

## Background: Image

https://www.raspberrypi.com/software/
https://www.raspberrypi.com/software/operating-systems/
Raspberry Pi OS Lite
Release date: December 11th 2023
System: 64-bit
Kernel version: 6.1
Debian version: 12 (bookworm)
Size: 433MB

## TASK: Create Image

Start: "Raspberry Pi Imager"

Select: Pi OS Lite (64-bit)
* `check` Set Hostname: `zero-virgin`
* `check` Enable SSH
  * `check` Use password authentication
* `check` Set username and password
  * Username `<622_pc_image_build-password.txt>`
  * Password `<622_pc_image_build-password.txt>`
* `uncheck` Configure wireless LAN
* `check` Set locale settings
  * Time Zone: `Europe/Zurich`
  * Keyboard layout: `gb`
