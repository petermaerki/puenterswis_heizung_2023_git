set -euox pipefail

# pip install -r /home/zero/puenterswis_heizung_2023_git/software/software-zero/requirements.txt
# export AUTOMATIK=/home/maerki/work_heizung/puenterswis_heizung_2023_git/software
export AUTOMATIK=/home/zero/puenterswis_heizung_2023_git/software
export PYTHONPATH=${AUTOMATIK}/software-zentral:${AUTOMATIK}/software-dezentral:${AUTOMATIK}/software-zero
export HEIZUNG2023_MOCKED=0
cd ${AUTOMATIK}/software-zentral

# Without fastapi
# python -m zentral.run_zentral

# With fastapi, but without debug/reload
source /home/zero/venv_app/bin/activate
python -m uvicorn zentral.run_zentral_fastapi:APP --workers=1 --port=8000 --host=0.0.0.0

echo $?
