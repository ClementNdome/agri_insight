from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class AreaOfInterest(models.Model):
    """Model for storing areas of interest drawn on the map"""
    
    name = models.CharField(max_length=255, help_text="Name of the area of interest")
    description = models.TextField(blank=True, null=True, help_text="Description of the area")
    geometry = models.PolygonField(srid=4326, help_text="Polygon geometry of the area")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='areas_of_interest')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Whether this area is actively monitored")
    
    # Metadata
    area_hectares = models.FloatField(null=True, blank=True, help_text="Area in hectares")
    centroid_lat = models.FloatField(null=True, blank=True, help_text="Centroid latitude")
    centroid_lon = models.FloatField(null=True, blank=True, help_text="Centroid longitude")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Area of Interest'
        verbose_name_plural = 'Areas of Interest'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.geometry:
            # Calculate area in hectares
            self.area_hectares = self.geometry.area * 10000  # Convert from square degrees to hectares (approximate)
            
            # Calculate centroid
            centroid = self.geometry.centroid
            self.centroid_lat = centroid.y
            self.centroid_lon = centroid.x
        
        super().save(*args, **kwargs)


class VegetationIndex(models.Model):
    """Model for storing different types of vegetation indices"""
    
    INDEX_TYPES = [
        ('NDVI', 'Normalized Difference Vegetation Index'),
        ('EVI', 'Enhanced Vegetation Index'),
        ('SAVI', 'Soil Adjusted Vegetation Index'),
        ('NDMI', 'Normalized Difference Moisture Index'),
        ('NBR', 'Normalized Burn Ratio'),
        ('NDWI', 'Normalized Difference Water Index'),
        ('GNDVI', 'Green Normalized Difference Vegetation Index'),
        ('OSAVI', 'Optimized Soil Adjusted Vegetation Index'),
    ]
    
    name = models.CharField(max_length=10, choices=INDEX_TYPES, unique=True)
    full_name = models.CharField(max_length=100)
    description = models.TextField(help_text="Description of what this index measures")
    formula = models.TextField(help_text="Mathematical formula for the index")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Vegetation Index'
        verbose_name_plural = 'Vegetation Indices'
    
    def __str__(self):
        return f"{self.name} - {self.full_name}"


class SatelliteImage(models.Model):
    """Model for storing satellite image metadata"""
    
    SATELLITE_CHOICES = [
        ('LANDSAT', 'Landsat'),
        ('SENTINEL2', 'Sentinel-2'),
        ('MODIS', 'MODIS'),
        ('SENTINEL1', 'Sentinel-1'),
    ]
    
    satellite = models.CharField(max_length=20, choices=SATELLITE_CHOICES)
    image_id = models.CharField(max_length=255, unique=True, help_text="Google Earth Engine image ID")
    acquisition_date = models.DateField(help_text="Date when the image was acquired")
    cloud_cover = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Cloud cover percentage"
    )
    resolution = models.FloatField(help_text="Spatial resolution in meters")
    bounds = models.PolygonField(srid=4326, help_text="Image bounds")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-acquisition_date']
        verbose_name = 'Satellite Image'
        verbose_name_plural = 'Satellite Images'
    
    def __str__(self):
        return f"{self.satellite} - {self.acquisition_date}"


class MonitoringData(models.Model):
    """Model for storing vegetation index monitoring data"""
    
    area_of_interest = models.ForeignKey(AreaOfInterest, on_delete=models.CASCADE, related_name='monitoring_data')
    vegetation_index = models.ForeignKey(VegetationIndex, on_delete=models.CASCADE, related_name='monitoring_data')
    satellite_image = models.ForeignKey(SatelliteImage, on_delete=models.CASCADE, related_name='monitoring_data')
    
    # Calculated values
    mean_value = models.FloatField(help_text="Mean value of the index for the area")
    min_value = models.FloatField(help_text="Minimum value of the index for the area")
    max_value = models.FloatField(help_text="Maximum value of the index for the area")
    std_value = models.FloatField(help_text="Standard deviation of the index for the area")
    pixel_count = models.IntegerField(help_text="Number of pixels in the area")
    
    # Metadata
    calculation_date = models.DateTimeField(auto_now_add=True)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PROCESSING', 'Processing'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed'),
        ],
        default='PENDING'
    )
    error_message = models.TextField(blank=True, null=True, help_text="Error message if processing failed")
    
    class Meta:
        ordering = ['-calculation_date']
        unique_together = ['area_of_interest', 'vegetation_index', 'satellite_image']
        verbose_name = 'Monitoring Data'
        verbose_name_plural = 'Monitoring Data'
    
    def __str__(self):
        return f"{self.area_of_interest.name} - {self.vegetation_index.name} - {self.satellite_image.acquisition_date}"


class MonitoringAlert(models.Model):
    """Model for storing monitoring alerts based on threshold values"""
    
    ALERT_TYPES = [
        ('THRESHOLD_LOW', 'Value below threshold'),
        ('THRESHOLD_HIGH', 'Value above threshold'),
        ('CHANGE_DETECTED', 'Significant change detected'),
        ('ANOMALY', 'Anomaly detected'),
    ]
    
    area_of_interest = models.ForeignKey(AreaOfInterest, on_delete=models.CASCADE, related_name='alerts')
    vegetation_index = models.ForeignKey(VegetationIndex, on_delete=models.CASCADE, related_name='alerts')
    monitoring_data = models.ForeignKey(MonitoringData, on_delete=models.CASCADE, related_name='alerts')
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField(help_text="Alert message")
    threshold_value = models.FloatField(null=True, blank=True, help_text="Threshold value that triggered the alert")
    actual_value = models.FloatField(help_text="Actual value that triggered the alert")
    severity = models.CharField(
        max_length=10,
        choices=[
            ('LOW', 'Low'),
            ('MEDIUM', 'Medium'),
            ('HIGH', 'High'),
            ('CRITICAL', 'Critical'),
        ],
        default='MEDIUM'
    )
    
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Monitoring Alert'
        verbose_name_plural = 'Monitoring Alerts'
    
    def __str__(self):
        return f"{self.area_of_interest.name} - {self.alert_type} - {self.created_at}"


class MonitoringConfiguration(models.Model):
    """Model for storing monitoring configuration settings"""
    
    area_of_interest = models.ForeignKey(AreaOfInterest, on_delete=models.CASCADE, related_name='configurations')
    vegetation_index = models.ForeignKey(VegetationIndex, on_delete=models.CASCADE, related_name='configurations')
    
    # Monitoring settings
    is_enabled = models.BooleanField(default=True, help_text="Whether monitoring is enabled for this combination")
    monitoring_frequency_days = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text="How often to monitor in days"
    )
    
    # Alert thresholds
    low_threshold = models.FloatField(null=True, blank=True, help_text="Low threshold for alerts")
    high_threshold = models.FloatField(null=True, blank=True, help_text="High threshold for alerts")
    change_threshold_percent = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage change threshold for alerts"
    )
    
    # Data processing settings
    cloud_cover_threshold = models.FloatField(
        default=20,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Maximum cloud cover percentage to use image"
    )
    min_pixel_count = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        help_text="Minimum number of pixels required for analysis"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['area_of_interest', 'vegetation_index']
        verbose_name = 'Monitoring Configuration'
        verbose_name_plural = 'Monitoring Configurations'
    
    def __str__(self):
        return f"{self.area_of_interest.name} - {self.vegetation_index.name}"
