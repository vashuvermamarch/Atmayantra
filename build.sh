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
  # The root cause is likely an inconsistent initial migration.
  # We will fake the initial state for the problematic app.
  python manage.py migrate --fake doctor_personal_details zero
  echo "Faking complete. Retrying full migration..."
  python manage.py migrate
}