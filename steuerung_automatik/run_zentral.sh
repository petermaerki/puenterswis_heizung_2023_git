# pip install -r /home/zero/puenterswis_heizung_2023_git/steuerung_automatik/software-zero/requirements.txt

export PYTHONPATH=/home/zero/puenterswis_heizung_2023_git/steuerung_automatik/software-zentral:/home/zero/puenterswis_heizung_2023_git/steuerung_automatik/software-dezentral
cd /home/zero/puenterswis_heizung_2023_git/steuerung_automatik/software-zentral
python -m zentral.run_zentral
