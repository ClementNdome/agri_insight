"""
ASGI config for agri_insight project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forest_monitoring.settings')

application = get_asgi_application()
