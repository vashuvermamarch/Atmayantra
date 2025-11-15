#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt 

# These commands are run from the project root
python Atmayantra/manage.py collectstatic --no-input
python Atmayantra/manage.py migrate