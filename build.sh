#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# RUN FROM ROOT WHERE manage.py EXISTS
python Atmayantra/manage.py collectstatic --no-input
python Atmayantra/manage.py migrate
