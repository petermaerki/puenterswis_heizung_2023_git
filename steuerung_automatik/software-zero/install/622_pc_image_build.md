# Installation SDCARD

Goal: Create configured SD card, ssh via ethernet

## Background: Image

https://www.raspberrypi.com/software/
https://www.raspberrypi.com/software/operating-systems/
Raspberry Pi OS Lite
Release date: 2024-03-15
System: 64-bit
Kernel version: 6.1
Debian version: 12 (bookworm)
Size: 433MB

## TASK: Create Image

Start: "Raspberry Pi Imager"

Select: Pi OS Lite (64-bit)
* General
  * `check` Set Hostname: `zero-virgin`
  * `check` Set username and password
    * Username `<622_pc_image_build-password.txt>`
    * Password `<622_pc_image_build-password.txt>`
  * `uncheck` Configure wireless LAN
  * `check` Set locale settings
    * Time Zone: `Europe/Zurich`
    * Keyboard layout: `us`
* Services
  * `check` Enable SSH
    * `check` Use password authentication


## Boot Rasperry

```bash
watch ping -c 1 zero-virgin.local

ssh zero@zero-virgin.local
```
