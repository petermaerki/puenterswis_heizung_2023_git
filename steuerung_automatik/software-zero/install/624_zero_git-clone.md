# Git Clone

Goal:
* Clone git
* security bootstrap

## TASK: ssh

PC:
```
ssh zero@zero-virgin
```

Use password authentication!

## TASK: apt update/install

zero:
```
LC_ALL=en_GB.UTF-8 sudo apt update \
  && sudo apt upgrade -y && sudo apt install -y python3-pip git \
  && sudo apt autoremove -y
```


## TASK: Git Clone

PC:
```
cd /home/zero
git clone https://github.com/petermaerki/puenterswis_heizung_2023_git.git
```
