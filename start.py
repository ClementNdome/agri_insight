#!/usr/bin/env python
"""
Startup script for AgriInsight - Geospatial Agriculture Data Platform
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_environment():
    """Check if the environment is properly set up"""
    print("Checking environment...")
    
    # Check if virtual environment exists
    if not os.path.exists('venv'):
        print("✗ Virtual environment not found. Please run setup.py first.")
        return False
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("✗ .env file not found. Please run setup.py first.")
        return False
    
    # Check if database migrations are up to date
    if sys.platform == 'win32':
        python_executable = 'venv\\Scripts\\python.exe'
    else:
        python_executable = 'venv/bin/python'
    
    try:
        result = subprocess.run(
            f'{python_executable} manage.py showmigrations --plan | grep "\\[ \\]"',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            print("⚠ Warning: There are unapplied migrations. Run 'python manage.py migrate' first.")
    except:
        pass  # Ignore errors in migration check
    
    print("✓ Environment check completed")
    return True

def start_services():
    """Start the required services"""
    print("Starting services...")
    
    if sys.platform == 'win32':
        python_executable = 'venv\\Scripts\\python.exe'
    else:
        python_executable = 'venv/bin/python'
    
    # Start Redis (if not running)
    print("Checking Redis...")
    try:
        subprocess.run('redis-cli ping', shell=True, check=True, capture_output=True)
        print("✓ Redis is running")
    except subprocess.CalledProcessError:
        print("⚠ Redis is not running. Please start Redis before running the application.")
        print("  On Windows: Download and run Redis server")
        print("  On Linux: sudo systemctl start redis")
        print("  On macOS: brew services start redis")
        return False
    
    # Start Celery worker in background
    print("Starting Celery worker...")
    celery_process = subprocess.Popen(
        f'{python_executable} -m celery -A monitoring worker -l info',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give Celery time to start
    time.sleep(2)
    
    # Start Django development server
    print("Starting Django development server...")
    print("=" * 50)
    print("AgriInsight - Geospatial Agriculture Data Platform is starting...")
    print("Access the application at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start Django server (this will block)
        subprocess.run(f'{python_executable} manage.py runserver', shell=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
        celery_process.terminate()
        print("✓ Services stopped")

def main():
    """Main startup function"""
    print("AgriInsight - Geospatial Agriculture Data Platform Startup")
    print("=" * 40)
    
    if not check_environment():
        sys.exit(1)
    
    start_services()

if __name__ == '__main__':
    main()
