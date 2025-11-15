"""
URL configuration for agri_insight project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from monitoring import views as monitoring_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('api/', include('monitoring.urls')),
    path('landing/', monitoring_views.LandingView.as_view(), name='landing'),
    path('demo/', monitoring_views.DemoView.as_view(), name='demo'),
    path('', monitoring_views.HomeView.as_view(), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
