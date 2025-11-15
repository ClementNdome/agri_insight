"""
WSGI config for agri_insight project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agri_insight.settings')

application = get_wsgi_application()