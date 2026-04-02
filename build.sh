#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Enter the folder where manage.py is located
cd Atmayantra

python manage.py collectstatic --no-input
python manage.py makemigrations 
python manage.py migrate --noinput

# Create Cache Table for Database Tracking (Required for Render)
python manage.py createcachetable

# Create admin user
python create_admin.py
