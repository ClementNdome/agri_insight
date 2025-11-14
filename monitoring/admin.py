from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import (
    AreaOfInterest, VegetationIndex, SatelliteImage,
    MonitoringData, MonitoringAlert, MonitoringConfiguration, Tip
)


@admin.register(AreaOfInterest)
class AreaOfInterestAdmin(GISModelAdmin):
    list_display = ['name', 'created_by', 'area_hectares', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['area_hectares', 'centroid_lat', 'centroid_lon', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'created_by', 'is_active')
        }),
        ('Geometry', {
            'fields': ('geometry',)
        }),
        ('Calculated Properties', {
            'fields': ('area_hectares', 'centroid_lat', 'centroid_lon'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VegetationIndex)
class VegetationIndexAdmin(admin.ModelAdmin):
    list_display = ['name', 'full_name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'full_name', 'description']


@admin.register(SatelliteImage)
class SatelliteImageAdmin(admin.ModelAdmin):
    list_display = ['satellite', 'acquisition_date', 'cloud_cover', 'resolution', 'created_at']
    list_filter = ['satellite', 'acquisition_date', 'cloud_cover']
    search_fields = ['image_id', 'satellite']
    readonly_fields = ['created_at']


@admin.register(MonitoringData)
class MonitoringDataAdmin(admin.ModelAdmin):
    list_display = [
        'area_of_interest', 'vegetation_index', 'satellite_image', 
        'mean_value', 'processing_status', 'calculation_date'
    ]
    list_filter = [
        'processing_status', 'calculation_date', 'vegetation_index', 
        'satellite_image__satellite'
    ]
    search_fields = [
        'area_of_interest__name', 'vegetation_index__name', 
        'satellite_image__image_id'
    ]
    readonly_fields = ['calculation_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('area_of_interest', 'vegetation_index', 'satellite_image')
        }),
        ('Calculated Values', {
            'fields': ('mean_value', 'min_value', 'max_value', 'std_value', 'pixel_count')
        }),
        ('Processing Information', {
            'fields': ('processing_status', 'error_message', 'calculation_date')
        }),
    )


@admin.register(MonitoringAlert)
class MonitoringAlertAdmin(admin.ModelAdmin):
    list_display = [
        'area_of_interest', 'vegetation_index', 'alert_type', 
        'severity', 'is_resolved', 'created_at'
    ]
    list_filter = [
        'alert_type', 'severity', 'is_resolved', 'created_at', 
        'vegetation_index'
    ]
    search_fields = ['area_of_interest__name', 'message']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('area_of_interest', 'vegetation_index', 'monitoring_data', 'alert_type')
        }),
        ('Alert Details', {
            'fields': ('message', 'threshold_value', 'actual_value', 'severity')
        }),
        ('Status', {
            'fields': ('is_resolved', 'created_at', 'resolved_at')
        }),
    )


@admin.register(MonitoringConfiguration)
class MonitoringConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'area_of_interest', 'vegetation_index', 'is_enabled', 
        'monitoring_frequency_days', 'updated_at'
    ]
    list_filter = ['is_enabled', 'vegetation_index', 'monitoring_frequency_days']
    search_fields = ['area_of_interest__name', 'vegetation_index__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('area_of_interest', 'vegetation_index', 'is_enabled', 'monitoring_frequency_days')
        }),
        ('Alert Thresholds', {
            'fields': ('low_threshold', 'high_threshold', 'change_threshold_percent')
        }),
        ('Data Processing Settings', {
            'fields': ('cloud_cover_threshold', 'min_pixel_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_active', 'order', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Tip Information', {
            'fields': ('title', 'content', 'category', 'image_url')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
