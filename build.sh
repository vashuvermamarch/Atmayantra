#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Change to the directory where manage.py is located for robustness
cd Atmayantra

python manage.py collectstatic --no-input --clear

# Run migrations, but if it fails, fake the problematic migration and try again.
# This is a common fix for inconsistent migration history during deployment.
python manage.py migrate || {
  echo "Initial migration failed. Faking problematic migrations..."
  # 1. Reset the state for the app with the missing table.
  python manage.py migrate --fake doctor_personal_details zero
  # 2. Apply migrations for ONLY that app to bring it to a consistent state.
  python manage.py migrate doctor_personal_details
  echo "Recovery for doctor_personal_details complete. Retrying migrations for all other apps..."
  # 3. Run a final migration for any remaining apps.
  python manage.py migrate
}