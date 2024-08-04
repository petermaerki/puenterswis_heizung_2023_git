# https://www.ics.com/blog/gpio-programming-using-sysfs-interface

echo 24 >/sys/class/gpio/export
echo in >/sys/class/gpio/gpio24/direction
cat /sys/class/gpio/gpio24/value


https://www.raspberrypi.com/documentation/computers/compute-module.html

GOAL:
GPIO26: Output, ground
GPIO20: Input, pullup, puent
GPIO21: Input, pullup, bochs

pinctrl help

## Initialize the gpio
pinctrl set 26 op dl
pinctrl set 20 ip pu
pinctrl set 21 ip pu

pinctrl get 20,21

## Read the gpio
echo 20 >/sys/class/gpio/export
echo 21 >/sys/class/gpio/export

cat /sys/class/gpio/gpio20/value /sys/class/gpio/gpio21/value

