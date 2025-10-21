#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

cd Atmayantra
python manage.py collectstatic --noinput
python manage.py migrate