from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.gis.geos import GEOSGeometry
from .models import AreaOfInterest, MonitoringData, MonitoringConfiguration
from .tasks import check_alerts


@receiver(post_save, sender=AreaOfInterest)
def calculate_area_properties(sender, instance, created, **kwargs):
    """Calculate area properties when an AreaOfInterest is saved"""
    if instance.geometry:
        # Calculate area in hectares (approximate conversion from square degrees)
        # This is a rough approximation - for production, use proper projection
        instance.area_hectares = instance.geometry.area * 10000
        
        # Calculate centroid
        centroid = instance.geometry.centroid
        instance.centroid_lat = centroid.y
        instance.centroid_lon = centroid.x
        
        # Save without triggering signals again
        AreaOfInterest.objects.filter(pk=instance.pk).update(
            area_hectares=instance.area_hectares,
            centroid_lat=instance.centroid_lat,
            centroid_lon=instance.centroid_lon
        )


@receiver(post_save, sender=MonitoringData)
def trigger_alert_check(sender, instance, created, **kwargs):
    """Trigger alert checking when new monitoring data is created"""
    if created and instance.processing_status == 'COMPLETED':
        # Check if there's a configuration for this area and vegetation index
        try:
            config = MonitoringConfiguration.objects.get(
                area_of_interest=instance.area_of_interest,
                vegetation_index=instance.vegetation_index,
                is_enabled=True
            )
            # Trigger alert checking asynchronously
            check_alerts.delay(instance.id)
        except MonitoringConfiguration.DoesNotExist:
            pass  # No configuration, no alerts to check


@receiver(post_save, sender=MonitoringConfiguration)
def create_default_configuration(sender, instance, created, **kwargs):
    """Set default values for new monitoring configurations"""
    if created:
        # Set default monitoring frequency if not specified
        if not instance.monitoring_frequency_days:
            instance.monitoring_frequency_days = 30
        
        # Set default cloud cover threshold if not specified
        if not instance.cloud_cover_threshold:
            instance.cloud_cover_threshold = 20
        
        # Set default minimum pixel count if not specified
        if not instance.min_pixel_count:
            instance.min_pixel_count = 10
        
        # Save the instance with default values
        instance.save()
