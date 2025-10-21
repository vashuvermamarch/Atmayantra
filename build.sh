#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

cd Atmayantra
pwd
echo $PYTHONPATH
python -c "import sys; print(sys.path)"
python manage.py collectstatic --noinput
python manage.py migrate