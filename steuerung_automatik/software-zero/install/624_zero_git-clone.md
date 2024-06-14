# Git Clone

Goal:
* Clone git
* security bootstrap

## TASK: ssh

PC:
```
ssh zero@zero-virgin.local
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

zero:
```
cd /home/zero
git clone https://github.com/petermaerki/puenterswis_heizung_2023_git.git
```

## TASK: copy `config_secrets.py`

zero:
```
cat > /home/zero/puenterswis_heizung_2023_git/steuerung_automatik/software-zentral/zentral/config_secrets.py
```

## TASK: Python venv and pip

zero:
```
python -m venv /home/zero/venv_app

source /home/zero/venv_app/bin/activate
pip install --upgrade -r /home/zero/puenterswis_heizung_2023_git/steuerung_automatik/software-zero/requirements.txt
```

