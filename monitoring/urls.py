from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'areas', views.AreaOfInterestViewSet, basename='areaofinterest')
router.register(r'vegetation-indices', views.VegetationIndexViewSet, basename='vegetationindex')
router.register(r'satellite-images', views.SatelliteImageViewSet, basename='satelliteimage')
router.register(r'monitoring-data', views.MonitoringDataViewSet, basename='monitoringdata')
router.register(r'alerts', views.MonitoringAlertViewSet, basename='monitoringalert')
router.register(r'configurations', views.MonitoringConfigurationViewSet, basename='monitoringconfiguration')

urlpatterns = [
    path('', include(router.urls)),
]
