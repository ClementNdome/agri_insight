from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'areas', views.AreaOfInterestViewSet)
router.register(r'vegetation-indices', views.VegetationIndexViewSet)
router.register(r'satellite-images', views.SatelliteImageViewSet)
router.register(r'monitoring-data', views.MonitoringDataViewSet)
router.register(r'alerts', views.MonitoringAlertViewSet)
router.register(r'configurations', views.MonitoringConfigurationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
