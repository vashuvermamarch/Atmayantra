#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Enter the folder where manage.py is located
cd Atmayantra

python manage.py collectstatic --no-input
python manage.py makemigrations 
python manage.py migrate --noinput

# Create admin user
python create_admin.py
