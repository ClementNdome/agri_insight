#!/usr/bin/env bash
# build.sh

# Upgrade pip
pip install --upgrade pip

# Install setuptools and wheel first
pip install setuptools==69.0.2 wheel==0.42.0

# Then install the rest of requirements
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate