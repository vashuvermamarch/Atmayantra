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
  # The database is in an inconsistent state. We will "fake" the initial
  # migrations for all apps to align Django's state with the database.
  python manage.py migrate --fake-initial
  echo "Faking initial migrations complete. Retrying full migration..."
  # Now, run migrate again. It will skip the faked initial migrations
  # and apply any subsequent ones.
  python manage.py migrate
}