#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python Atmayantra/manage.py collectstatic --noinput
python Atmayantra/manage.py migrate
