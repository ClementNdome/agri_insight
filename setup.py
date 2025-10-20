#!/usr/bin/env python
"""
Setup script for Forest Monitoring System
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_dependencies():
    """Check if required system dependencies are available"""
    dependencies = {
        'postgresql': 'psql --version',
        'redis': 'redis-server --version',
        'gdal': 'gdalinfo --version'
    }
    
    missing = []
    for name, command in dependencies.items():
        if not run_command(command, f"Checking {name}"):
            missing.append(name)
    
    if missing:
        print(f"✗ Missing dependencies: {', '.join(missing)}")
        print("Please install the missing dependencies before continuing")
        return False
    
    return True

def create_virtual_environment():
    """Create virtual environment"""
    if os.path.exists('venv'):
        print("Virtual environment already exists")
        return True
    
    return run_command('python -m venv venv', 'Creating virtual environment')

def activate_virtual_environment():
    """Activate virtual environment"""
    if sys.platform == 'win32':
        activate_script = 'venv\\Scripts\\activate.bat'
        python_executable = 'venv\\Scripts\\python.exe'
        pip_executable = 'venv\\Scripts\\pip.exe'
    else:
        activate_script = 'venv/bin/activate'
        python_executable = 'venv/bin/python'
        pip_executable = 'venv/bin/pip'
    
    return python_executable, pip_executable

def install_python_dependencies(pip_executable):
    """Install Python dependencies"""
    return run_command(f'{pip_executable} install -r requirements.txt', 'Installing Python dependencies')

def create_env_file():
    """Create .env file from template"""
    if os.path.exists('.env'):
        print(".env file already exists")
        return True
    
    if os.path.exists('env.example'):
        shutil.copy('env.example', '.env')
        print("✓ Created .env file from template")
        print("Please edit .env file with your configuration")
        return True
    else:
        print("✗ env.example file not found")
        return False

def setup_database(python_executable):
    """Set up database"""
    commands = [
        (f'{python_executable} manage.py makemigrations', 'Creating database migrations'),
        (f'{python_executable} manage.py migrate', 'Applying database migrations'),
        (f'{python_executable} manage.py init_vegetation_indices', 'Initializing vegetation indices'),
        (f'{python_executable} manage.py createsuperuser', 'Creating superuser (interactive)')
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'static', 'media']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True

def main():
    """Main setup function"""
    print("Forest Monitoring System Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check system dependencies
    print("\nChecking system dependencies...")
    if not check_dependencies():
        print("\nPlease install the missing dependencies and run setup again")
        sys.exit(1)
    
    # Create virtual environment
    print("\nSetting up Python environment...")
    if not create_virtual_environment():
        sys.exit(1)
    
    # Get executable paths
    python_executable, pip_executable = activate_virtual_environment()
    
    # Install Python dependencies
    if not install_python_dependencies(pip_executable):
        sys.exit(1)
    
    # Create .env file
    print("\nSetting up configuration...")
    if not create_env_file():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Set up database
    print("\nSetting up database...")
    if not setup_database(python_executable):
        print("Database setup failed. Please check your database configuration in .env file")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Set up Google Earth Engine credentials")
    print("3. Start the development server:")
    print(f"   {python_executable} manage.py runserver")
    print("\nFor production deployment, see README.md")

if __name__ == '__main__':
    main()
