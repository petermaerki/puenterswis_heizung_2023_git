# pip install -r /home/zero/puenterswis_heizung_2023_git/steuerung_automatik/software-zero/requirements.txt
# export AUTOMATIK=/home/maerki/work_heizung/puenterswis_heizung_2023_git/steuerung_automatik
export AUTOMATIK=/home/zero/puenterswis_heizung_2023_git/steuerung_automatik
export PYTHONPATH=${AUTOMATIK}/software-zentral:${AUTOMATIK}/software-dezentral
cd ${AUTOMATIK}/software-zentral
python -m zentral.run_zentral
echo $?
