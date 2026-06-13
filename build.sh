#!/bin/bash
echo "Installing python dependencies..."
python3.12 -m pip install -r requirements.txt

echo "Running Django collectstatic..."
python3.12 manage.py collectstatic --noinput

echo "Running migrations..."
python3.12 manage.py migrate --noinput
