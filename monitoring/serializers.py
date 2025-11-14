import json
from rest_framework import serializers
from django.contrib.gis.geos import GEOSGeometry
from .models import (
    AreaOfInterest, VegetationIndex, SatelliteImage, 
    MonitoringData, MonitoringAlert, MonitoringConfiguration
)


class AreaOfInterestSerializer(serializers.ModelSerializer):
    geometry_geojson = serializers.SerializerMethodField()
    area_hectares = serializers.ReadOnlyField()
    centroid_lat = serializers.ReadOnlyField()
    centroid_lon = serializers.ReadOnlyField()
    
    class Meta:
        model = AreaOfInterest
        fields = [
            'id', 'name', 'description', 'geometry', 'geometry_geojson',
            'created_by', 'created_at', 'updated_at', 'is_active',
            'area_hectares', 'centroid_lat', 'centroid_lon'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_geometry_geojson(self, obj):
        """Convert geometry to GeoJSON format"""
        if obj.geometry:
            return json.loads(obj.geometry.geojson)
        return None
    
    def create(self, validated_data):
        """Create a new area of interest"""
        # Handle anonymous users by creating a default user or using a system user
        user = self.context['request'].user
        if not user.is_authenticated:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user, created = User.objects.get_or_create(
                username='anonymous',
                defaults={'email': 'anonymous@example.com'}
            )
        validated_data['created_by'] = user
        return super().create(validated_data)


class VegetationIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = VegetationIndex
        fields = ['id', 'name', 'full_name', 'description', 'formula', 'is_active']


class SatelliteImageSerializer(serializers.ModelSerializer):
    bounds_geojson = serializers.SerializerMethodField()
    
    class Meta:
        model = SatelliteImage
        fields = [
            'id', 'satellite', 'image_id', 'acquisition_date', 
            'cloud_cover', 'resolution', 'bounds', 'bounds_geojson', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_bounds_geojson(self, obj):
        """Convert bounds to GeoJSON format"""
        if obj.bounds:
            return json.loads(obj.bounds.geojson)
        return None


class MonitoringDataSerializer(serializers.ModelSerializer):
    area_of_interest_name = serializers.CharField(source='area_of_interest.name', read_only=True)
    vegetation_index_name = serializers.CharField(source='vegetation_index.name', read_only=True)
    satellite_image_id = serializers.CharField(source='satellite_image.image_id', read_only=True)
    acquisition_date = serializers.DateField(source='satellite_image.acquisition_date', read_only=True)
    
    class Meta:
        model = MonitoringData
        fields = [
            'id', 'area_of_interest', 'area_of_interest_name',
            'vegetation_index', 'vegetation_index_name',
            'satellite_image', 'satellite_image_id', 'acquisition_date',
            'mean_value', 'min_value', 'max_value', 'std_value', 'pixel_count',
            'calculation_date', 'processing_status', 'error_message'
        ]
        read_only_fields = ['calculation_date']


class MonitoringAlertSerializer(serializers.ModelSerializer):
    area_of_interest_name = serializers.CharField(source='area_of_interest.name', read_only=True)
    vegetation_index_name = serializers.CharField(source='vegetation_index.name', read_only=True)
    
    class Meta:
        model = MonitoringAlert
        fields = [
            'id', 'area_of_interest', 'area_of_interest_name',
            'vegetation_index', 'vegetation_index_name',
            'monitoring_data', 'alert_type', 'message',
            'threshold_value', 'actual_value', 'severity',
            'is_resolved', 'created_at', 'resolved_at'
        ]
        read_only_fields = ['created_at']


class MonitoringConfigurationSerializer(serializers.ModelSerializer):
    area_of_interest_name = serializers.CharField(source='area_of_interest.name', read_only=True)
    vegetation_index_name = serializers.CharField(source='vegetation_index.name', read_only=True)
    
    class Meta:
        model = MonitoringConfiguration
        fields = [
            'id', 'area_of_interest', 'area_of_interest_name',
            'vegetation_index', 'vegetation_index_name',
            'is_enabled', 'monitoring_frequency_days',
            'low_threshold', 'high_threshold', 'change_threshold_percent',
            'cloud_cover_threshold', 'min_pixel_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class MonitoringDataCreateSerializer(serializers.Serializer):
    """Serializer for creating monitoring data via API"""
    area_of_interest_id = serializers.IntegerField()
    vegetation_index_name = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    satellite = serializers.ChoiceField(choices=['SENTINEL2', 'LANDSAT', 'MODIS'], default='SENTINEL2')
    cloud_cover_threshold = serializers.FloatField(default=20.0, min_value=0, max_value=100)


class MonitoringVisualizationSerializer(serializers.Serializer):
    """Serializer for monitoring visualization requests"""
    area_of_interest_id = serializers.IntegerField()
    vegetation_index_name = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    satellite = serializers.ChoiceField(choices=['SENTINEL2', 'LANDSAT', 'MODIS'], default='SENTINEL2')


class AreaOfInterestCreateSerializer(serializers.Serializer):
    """Serializer for creating areas of interest with GeoJSON"""
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    geometry_geojson = serializers.DictField()
    
    def validate_geometry_geojson(self, value):
        """Validate that the GeoJSON is a valid polygon"""
        try:
            # Handle both Feature and Geometry objects
            if value.get('type') == 'Feature':
                geometry_data = value.get('geometry', {})
            else:
                geometry_data = value
                
            geometry = GEOSGeometry(json.dumps(geometry_data))
            if geometry.geom_type not in ['Polygon', 'MultiPolygon']:
                raise serializers.ValidationError("Geometry must be a Polygon or MultiPolygon")
            return geometry_data  # Return the geometry part, not the full Feature
        except Exception as e:
            raise serializers.ValidationError(f"Invalid GeoJSON: {e}")
    
    def create(self, validated_data):
        """Create area of interest from GeoJSON"""
        geometry_geojson = validated_data.pop('geometry_geojson')
        geometry = GEOSGeometry(json.dumps(geometry_geojson))
        
        validated_data['geometry'] = geometry
        
        # Handle anonymous users
        user = self.context['request'].user
        if not user.is_authenticated:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user, created = User.objects.get_or_create(
                username='anonymous',
                defaults={'email': 'anonymous@example.com'}
            )
        validated_data['created_by'] = user
        
        return AreaOfInterest.objects.create(**validated_data)
