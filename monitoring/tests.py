from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Polygon

User = get_user_model()
from django.utils import timezone
from .models import (
    AreaOfInterest, VegetationIndex, SatelliteImage, 
    MonitoringData, MonitoringAlert, MonitoringConfiguration
)
from .services import GoogleEarthEngineService, VegetationIndexCalculator
from .utils import (
    geojson_to_geos, geos_to_geojson, calculate_polygon_area_hectares,
    validate_geometry, calculate_vegetation_index_statistics
)


class AreaOfInterestModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a simple polygon
        self.polygon = Polygon([
            (0, 0), (1, 0), (1, 1), (0, 1), (0, 0)
        ])
    
    def test_create_area_of_interest(self):
        area = AreaOfInterest.objects.create(
            name='Test Area',
            description='A test area for monitoring',
            geometry=self.polygon,
            created_by=self.user
        )
        
        self.assertEqual(area.name, 'Test Area')
        self.assertEqual(area.created_by, self.user)
        self.assertTrue(area.is_active)
        self.assertIsNotNone(area.area_hectares)
        self.assertIsNotNone(area.centroid_lat)
        self.assertIsNotNone(area.centroid_lon)
    
    def test_area_calculation(self):
        area = AreaOfInterest.objects.create(
            name='Test Area',
            geometry=self.polygon,
            created_by=self.user
        )
        
        # Check that area and centroid were calculated
        self.assertGreater(area.area_hectares, 0)
        self.assertIsNotNone(area.centroid_lat)
        self.assertIsNotNone(area.centroid_lon)


class VegetationIndexModelTest(TestCase):
    def test_create_vegetation_index(self):
        index = VegetationIndex.objects.create(
            name='NDVI',
            full_name='Normalized Difference Vegetation Index',
            description='Measures vegetation health',
            formula='(NIR - Red) / (NIR + Red)'
        )
        
        self.assertEqual(index.name, 'NDVI')
        self.assertTrue(index.is_active)


class MonitoringDataModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.area = AreaOfInterest.objects.create(
            name='Test Area',
            geometry=Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
            created_by=self.user
        )
        
        self.vegetation_index = VegetationIndex.objects.create(
            name='NDVI',
            full_name='Normalized Difference Vegetation Index',
            description='Test index',
            formula='(NIR - Red) / (NIR + Red)'
        )
        
        self.satellite_image = SatelliteImage.objects.create(
            satellite='SENTINEL2',
            image_id='test_image_001',
            acquisition_date=timezone.now().date(),
            cloud_cover=10.0,
            resolution=30.0,
            bounds=self.area.geometry
        )
    
    def test_create_monitoring_data(self):
        monitoring_data = MonitoringData.objects.create(
            area_of_interest=self.area,
            vegetation_index=self.vegetation_index,
            satellite_image=self.satellite_image,
            mean_value=0.5,
            min_value=0.2,
            max_value=0.8,
            std_value=0.1,
            pixel_count=100
        )
        
        self.assertEqual(monitoring_data.mean_value, 0.5)
        self.assertEqual(monitoring_data.processing_status, 'PENDING')


class MonitoringAlertModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.area = AreaOfInterest.objects.create(
            name='Test Area',
            geometry=Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
            created_by=self.user
        )
        
        self.vegetation_index = VegetationIndex.objects.create(
            name='NDVI',
            full_name='Normalized Difference Vegetation Index',
            description='Test index',
            formula='(NIR - Red) / (NIR + Red)'
        )
        
        self.satellite_image = SatelliteImage.objects.create(
            satellite='SENTINEL2',
            image_id='test_image_001',
            acquisition_date=timezone.now().date(),
            cloud_cover=10.0,
            resolution=30.0,
            bounds=self.area.geometry
        )
        
        self.monitoring_data = MonitoringData.objects.create(
            area_of_interest=self.area,
            vegetation_index=self.vegetation_index,
            satellite_image=self.satellite_image,
            mean_value=0.5,
            min_value=0.2,
            max_value=0.8,
            std_value=0.1,
            pixel_count=100
        )
    
    def test_create_monitoring_alert(self):
        alert = MonitoringAlert.objects.create(
            area_of_interest=self.area,
            vegetation_index=self.vegetation_index,
            monitoring_data=self.monitoring_data,
            alert_type='THRESHOLD_LOW',
            message='Value below threshold',
            threshold_value=0.3,
            actual_value=0.2,
            severity='MEDIUM'
        )
        
        self.assertEqual(alert.alert_type, 'THRESHOLD_LOW')
        self.assertFalse(alert.is_resolved)


class MonitoringConfigurationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.area = AreaOfInterest.objects.create(
            name='Test Area',
            geometry=Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
            created_by=self.user
        )
        
        self.vegetation_index = VegetationIndex.objects.create(
            name='NDVI',
            full_name='Normalized Difference Vegetation Index',
            description='Test index',
            formula='(NIR - Red) / (NIR + Red)'
        )
    
    def test_create_monitoring_configuration(self):
        config = MonitoringConfiguration.objects.create(
            area_of_interest=self.area,
            vegetation_index=self.vegetation_index,
            is_enabled=True,
            monitoring_frequency_days=30,
            low_threshold=0.2,
            high_threshold=0.8,
            cloud_cover_threshold=20.0
        )
        
        self.assertTrue(config.is_enabled)
        self.assertEqual(config.monitoring_frequency_days, 30)
        self.assertEqual(config.low_threshold, 0.2)


class UtilityFunctionsTest(TestCase):
    def test_geojson_conversion(self):
        # Test GeoJSON to GEOSGeometry conversion
        geojson_data = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
        
        geos_geom = geojson_to_geos(geojson_data)
        self.assertEqual(geos_geom.geom_type, 'Polygon')
        
        # Test GEOSGeometry to GeoJSON conversion
        converted_geojson = geos_to_geojson(geos_geom)
        self.assertEqual(converted_geojson['type'], 'Polygon')
    
    def test_polygon_area_calculation(self):
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
        area = calculate_polygon_area_hectares(polygon)
        self.assertGreater(area, 0)
    
    def test_geometry_validation(self):
        # Valid polygon
        valid_polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
        self.assertTrue(validate_geometry(valid_polygon))
        
        # Invalid geometry (too small)
        small_polygon = Polygon([(0, 0), (0.0001, 0), (0.0001, 0.0001), (0, 0.0001), (0, 0)])
        self.assertFalse(validate_geometry(small_polygon))
    
    def test_vegetation_index_statistics(self):
        values = [0.1, 0.2, 0.3, 0.4, 0.5]
        stats = calculate_vegetation_index_statistics(values)
        
        self.assertEqual(stats['count'], 5)
        self.assertAlmostEqual(stats['mean'], 0.3, places=1)
        self.assertEqual(stats['min'], 0.1)
        self.assertEqual(stats['max'], 0.5)


class GoogleEarthEngineServiceTest(TestCase):
    def test_initialization(self):
        # Test service initialization (without actual EE authentication)
        service = GoogleEarthEngineService()
        # Note: This will fail without proper EE credentials, but we can test the structure
        self.assertIsNotNone(service)


class VegetationIndexCalculatorTest(TestCase):
    def test_initialization(self):
        calculator = VegetationIndexCalculator()
        self.assertIsNotNone(calculator)
        self.assertIsNotNone(calculator.ee_service)
