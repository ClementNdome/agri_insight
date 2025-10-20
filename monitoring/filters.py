import django_filters
from django.contrib.gis.geos import GEOSGeometry
from .models import AreaOfInterest, MonitoringData, MonitoringAlert, MonitoringConfiguration


class AreaOfInterestFilter(django_filters.FilterSet):
    """Filter for AreaOfInterest"""
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    area_min = django_filters.NumberFilter(field_name='area_hectares', lookup_expr='gte')
    area_max = django_filters.NumberFilter(field_name='area_hectares', lookup_expr='lte')
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = AreaOfInterest
        fields = ['name', 'description', 'is_active', 'created_by']


class MonitoringDataFilter(django_filters.FilterSet):
    """Filter for MonitoringData"""
    area_name = django_filters.CharFilter(field_name='area_of_interest__name', lookup_expr='icontains')
    vegetation_index_name = django_filters.CharFilter(field_name='vegetation_index__name')
    satellite = django_filters.CharFilter(field_name='satellite_image__satellite')
    acquisition_date_after = django_filters.DateFilter(field_name='satellite_image__acquisition_date', lookup_expr='gte')
    acquisition_date_before = django_filters.DateFilter(field_name='satellite_image__acquisition_date', lookup_expr='lte')
    mean_value_min = django_filters.NumberFilter(field_name='mean_value', lookup_expr='gte')
    mean_value_max = django_filters.NumberFilter(field_name='mean_value', lookup_expr='lte')
    calculation_date_after = django_filters.DateTimeFilter(field_name='calculation_date', lookup_expr='gte')
    calculation_date_before = django_filters.DateTimeFilter(field_name='calculation_date', lookup_expr='lte')
    
    class Meta:
        model = MonitoringData
        fields = ['area_of_interest', 'vegetation_index', 'processing_status']


class MonitoringAlertFilter(django_filters.FilterSet):
    """Filter for MonitoringAlert"""
    area_name = django_filters.CharFilter(field_name='area_of_interest__name', lookup_expr='icontains')
    vegetation_index_name = django_filters.CharFilter(field_name='vegetation_index__name')
    message = django_filters.CharFilter(lookup_expr='icontains')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    threshold_value_min = django_filters.NumberFilter(field_name='threshold_value', lookup_expr='gte')
    threshold_value_max = django_filters.NumberFilter(field_name='threshold_value', lookup_expr='lte')
    actual_value_min = django_filters.NumberFilter(field_name='actual_value', lookup_expr='gte')
    actual_value_max = django_filters.NumberFilter(field_name='actual_value', lookup_expr='lte')
    
    class Meta:
        model = MonitoringAlert
        fields = ['alert_type', 'severity', 'is_resolved', 'area_of_interest', 'vegetation_index']


class MonitoringConfigurationFilter(django_filters.FilterSet):
    """Filter for MonitoringConfiguration"""
    area_name = django_filters.CharFilter(field_name='area_of_interest__name', lookup_expr='icontains')
    vegetation_index_name = django_filters.CharFilter(field_name='vegetation_index__name')
    monitoring_frequency_min = django_filters.NumberFilter(field_name='monitoring_frequency_days', lookup_expr='gte')
    monitoring_frequency_max = django_filters.NumberFilter(field_name='monitoring_frequency_days', lookup_expr='lte')
    low_threshold_min = django_filters.NumberFilter(field_name='low_threshold', lookup_expr='gte')
    low_threshold_max = django_filters.NumberFilter(field_name='low_threshold', lookup_expr='lte')
    high_threshold_min = django_filters.NumberFilter(field_name='high_threshold', lookup_expr='gte')
    high_threshold_max = django_filters.NumberFilter(field_name='high_threshold', lookup_expr='lte')
    cloud_cover_threshold_min = django_filters.NumberFilter(field_name='cloud_cover_threshold', lookup_expr='gte')
    cloud_cover_threshold_max = django_filters.NumberFilter(field_name='cloud_cover_threshold', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = MonitoringConfiguration
        fields = ['is_enabled', 'area_of_interest', 'vegetation_index']
