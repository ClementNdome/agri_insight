#!/bin/bash
# Build script for Leapcell.io deployment
# This script runs during the build phase

set -e  # Exit on error

echo "Starting build process..."

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build completed successfully!"

