"""
Django settings for agri_insight project.
"""

import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ["*"]

# For deployment environments (e.g., leapcell.io), add dynamic hosts
if config('LEAPCELL_DEPLOYMENT', default=False, cast=bool) or config('PORT', default=None):
    leapcell_domain = config('LEAPCELL_DOMAIN', default=None) or config('HOST', default=None)
    if leapcell_domain:
        ALLOWED_HOSTS.append(leapcell_domain)

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rest_framework',
    'accounts',
    'monitoring',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'agri_insight.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'agri_insight.wsgi.application'

# Database - PostgreSQL with PostGIS
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'sslmode': config('DB_SSLMODE', default='require'),
        },
        'CONN_MAX_AGE': 600,
    }
}

# Optional: Add database URL support as fallback
DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.parse(
        DATABASE_URL,
        engine='django.contrib.gis.db.backends.postgis',
        conn_max_age=600,
    )

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Static files storage for production
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Login/Logout URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/landing/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# # GeoDjango settings - Only set library paths if needed
# if os.name == 'nt':  # Windows
#     GDAL_LIBRARY_PATH = config('GDAL_LIBRARY_PATH', default='C:/OSGeo4W/bin/gdal310.dll')
#     GEOS_LIBRARY_PATH = config('GEOS_LIBRARY_PATH', default='C:/OSGeo4W/bin/geos_c.dll')
# else:  # Linux/Production
#     GDAL_LIBRARY_PATH = config('GDAL_LIBRARY_PATH', default='/usr/lib/x86_64-linux-gnu/libgdal.so')
#     GEOS_LIBRARY_PATH = config('GEOS_LIBRARY_PATH', default='/usr/lib/x86_64-linux-gnu/libgeos_c.so')

# Google Earth Engine settings
GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH = config('GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH', default=None)
GOOGLE_EARTH_ENGINE_PROJECT = config('GOOGLE_EARTH_ENGINE_PROJECT', default=None)

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://app.spationex.com",
]
CSRF_TRUSTED_ORIGINS = [
    "https://app.spationex.com",
]

CORS_ALLOW_CREDENTIALS = True

# Leaflet settings
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (0.0, 0.0),
    'DEFAULT_ZOOM': 2,
    'MIN_ZOOM': 1,
    'MAX_ZOOM': 18,
    'DEFAULT_PRECISION': 6,
    'ATTRIBUTION_PREFIX': 'Agri Insight System',
    'RESET_VIEW': False,
    'SCALE': 'both',
    'MINIMAP': True,
}

# Celery settings
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Logging configuration - Console only for production (fixes read-only file system issue)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'monitoring': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Only add file logging in development if directory is writable
if DEBUG:
    try:
        logs_dir = BASE_DIR / 'logs'
        logs_dir.mkdir(exist_ok=True)
        # Test if we can write to the directory
        test_file = logs_dir / 'test_write.log'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        # Add file handler if writable
        LOGGING['handlers']['file'] = {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': logs_dir / 'django.log',
            'formatter': 'verbose',
        }
        LOGGING['root']['handlers'].append('file')
        LOGGING['loggers']['django']['handlers'].append('file')
        LOGGING['loggers']['monitoring']['handlers'].append('file')
    except (OSError, PermissionError):
        # If we can't write to files, just use console logging
        print("Warning: Cannot write to logs directory. Using console logging only.")

# Jazzmin Admin Configuration
JAZZMIN_SETTINGS = {
    "site_title": "Agri Insight Admin",
    "site_header": "Agri Insight",
    "site_brand": "Agri Insight",
    "site_logo_classes": "img-circle",
    "welcome_sign": "Welcome to Agri Insight Admin",
    "copyright": "Agri Insight Platform",
    "search_model": ["accounts.User", "monitoring.AreaOfInterest"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Visit Site", "url": "home", "new_window": True},
        {"model": "accounts.User"},
        {"app": "monitoring"},
    ],
    "usermenu_links": [
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "auth.user"}
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["accounts", "monitoring"],
    "custom_links": {
        "monitoring": [{
            "name": "View Site",
            "url": "/",
            "icon": "fas fa-globe",
            "permissions": ["monitoring.view_areaofinterest"]
        }]
    },
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "accounts.User": "fas fa-user-circle",
        "monitoring.AreaOfInterest": "fas fa-map-marked-alt",
        "monitoring.VegetationIndex": "fas fa-leaf",
        "monitoring.SatelliteImage": "fas fa-satellite",
        "monitoring.MonitoringData": "fas fa-chart-line",
        "monitoring.MonitoringAlert": "fas fa-bell",
        "monitoring.MonitoringConfiguration": "fas fa-cog",
        "monitoring.Tip": "fas fa-lightbulb",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": True,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs"
    },
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
    "actions_sticky_top": False
}