sudo iwlist wlan0 scan
sudo wpa_cli -i wlan0 reconfigure
sudo wpa_cli list_sta
sudo wpa_cli all_sta
sudo wpa_cli list_networks
sudo wpa_cli interface_list
sudo wpa_cli select_network <network id>
sudo wpa_cli enable_network <network id>
sudo systemctl restart wpa_supplicant.service
sudo systemctl restart dhcpcd.service
ifconfig
sudo journalctl -u wpa_supplicant.service



sudo /usr/lib/raspberrypi-sys-mods/imager_custom set_hostname 
sudo /usr/lib/raspberrypi-sys-mods/imager_custom set_wlan -p ssi pw CH

sudo raspi-config nonint do_hostname zero-bochs
sudo raspi-config nonint do_change_locale en_US.UTF-8
sudo raspi-config nonint do_change_timezone 'Europe/Zurich'
sudo raspi-config nonint do_wifi_country CH
sudo raspi-config nonint do_wifi_ssid_passphrase ssid pw 1 1
1 1: hidden plain

