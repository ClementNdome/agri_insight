#!/usr/bin/env python
"""
Deployment script for AgriInsight - Geospatial Agriculture Data Platform
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description, check=True):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def collect_static_files(python_executable):
    """Collect static files for production"""
    return run_command(
        f'{python_executable} manage.py collectstatic --noinput',
        'Collecting static files'
    )

def run_migrations(python_executable):
    """Run database migrations"""
    return run_command(
        f'{python_executable} manage.py migrate',
        'Running database migrations'
    )

def create_superuser(python_executable):
    """Create superuser if it doesn't exist"""
    # Check if superuser exists
    check_command = f'{python_executable} manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())"'
    result = subprocess.run(check_command, shell=True, capture_output=True, text=True)
    
    if 'True' in result.stdout:
        print("✓ Superuser already exists")
        return True
    
    print("Creating superuser...")
    print("Please provide the following information:")
    return run_command(
        f'{python_executable} manage.py createsuperuser',
        'Creating superuser',
        check=False
    )

def setup_logging():
    """Set up logging directories"""
    log_dirs = ['logs', 'logs/django', 'logs/celery']
    
    for log_dir in log_dirs:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created log directory: {log_dir}")
    
    return True

def setup_nginx_config():
    """Create nginx configuration template"""
    nginx_config = """
server {
    listen 80;
    server_name your-domain.com;
    
    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/your/project/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
    
    with open('nginx.conf', 'w') as f:
        f.write(nginx_config)
    
    print("✓ Created nginx configuration template")
    return True

def setup_systemd_services():
    """Create systemd service files"""
    
    # Django service
    django_service = """
[Unit]
Description=AgriInsight - Geospatial Agriculture Data Platform
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/project
Environment=DJANGO_SETTINGS_MODULE=forest_monitoring.settings
ExecStart=/path/to/your/project/venv/bin/gunicorn --bind 127.0.0.1:8000 forest_monitoring.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
"""
    
    # Celery service
    celery_service = """
[Unit]
Description=AgriInsight - Geospatial Agriculture Data Platform Celery Worker
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/project
Environment=DJANGO_SETTINGS_MODULE=forest_monitoring.settings
ExecStart=/path/to/your/project/venv/bin/celery -A forest_monitoring worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
"""
    
    # Celery Beat service
    celery_beat_service = """
[Unit]
Description=FAgriInsight - Geospatial Agriculture Data Platform Celery Beat
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/project
Environment=DJANGO_SETTINGS_MODULE=forest_monitoring.settings
ExecStart=/path/to/your/project/venv/bin/celery -A forest_monitoring beat -l info
Restart=always

[Install]
WantedBy=multi-user.target
"""
    
    with open('forest-monitoring.service', 'w') as f:
        f.write(django_service)
    
    with open('forest-monitoring-celery.service', 'w') as f:
        f.write(celery_service)
    
    with open('forest-monitoring-celery-beat.service', 'w') as f:
        f.write(celery_beat_service)
    
    print("✓ Created systemd service files")
    return True

def create_production_settings():
    """Create production settings file"""
    production_settings = """
# Production settings for AgriInsight - Geospatial Agriculture Data Platform
import os
from .settings import *

# Security settings
DEBUG = False
ALLOWED_HOSTS = ['*']

# Database settings (use environment variables)
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email settings (configure for your email provider)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# Celery settings
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
    }
}
"""
    
    with open('forest_monitoring/production_settings.py', 'w') as f:
        f.write(production_settings)
    
    print("✓ Created production settings file")
    return True

def main():
    """Main deployment function"""
    print("AgriInsight - Geospatial Agriculture Data Platform")
    print("=" * 40)
    
    # Get executable paths
    if sys.platform == 'win32':
        python_executable = 'venv\\Scripts\\python.exe'
    else:
        python_executable = 'venv/bin/python'
    
    # Check if virtual environment exists
    if not os.path.exists('venv'):
        print("✗ Virtual environment not found. Please run setup.py first.")
        sys.exit(1)
    
    # Set up logging
    print("\nSetting up logging...")
    if not setup_logging():
        sys.exit(1)
    
    # Run migrations
    print("\nRunning database migrations...")
    if not run_migrations(python_executable):
        sys.exit(1)
    
    # Create superuser
    print("\nSetting up superuser...")
    if not create_superuser(python_executable):
        print("Warning: Superuser creation failed or was skipped")
    
    # Collect static files
    print("\nCollecting static files...")
    if not collect_static_files(python_executable):
        sys.exit(1)
    
    # Create production configuration files
    print("\nCreating production configuration...")
    if not setup_nginx_config():
        sys.exit(1)
    
    if not setup_systemd_services():
        sys.exit(1)
    
    if not create_production_settings():
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("Deployment preparation completed!")
    print("\nNext steps for production deployment:")
    print("1. Copy the generated service files to /etc/systemd/system/")
    print("2. Copy nginx.conf to /etc/nginx/sites-available/")
    print("3. Enable and start the services:")
    print("   sudo systemctl enable forest-monitoring.service")
    print("   sudo systemctl enable forest-monitoring-celery.service")
    print("   sudo systemctl enable forest-monitoring-celery-beat.service")
    print("   sudo systemctl start forest-monitoring.service")
    print("   sudo systemctl start forest-monitoring-celery.service")
    print("   sudo systemctl start forest-monitoring-celery-beat.service")
    print("4. Configure nginx and restart it")
    print("5. Set up SSL certificates")
    print("6. Configure firewall rules")
    print("\nFor Docker deployment, use: docker-compose up -d")

if __name__ == '__main__':
    main()
