"""
WSGI config for forest_monitoring project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forest_monitoring.settings')

application = get_wsgi_application()
