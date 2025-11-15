#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python Atmayantra/manage.py collectstatic --no-input --clear

# Run migrations, but if it fails, fake the problematic migration and try again.
# This is a common fix for inconsistent migration history during deployment.
python Atmayantra/manage.py migrate || ( \
  python Atmayantra/manage.py migrate --fake doctor_bank_details 0002_remove_doctorbankdetails_profile_photo_and_more && \
  python Atmayantra/manage.py migrate )