import ee
try:
    import geemap
    GEEMAP_AVAILABLE = True
except ImportError:
    GEEMAP_AVAILABLE = False
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from shapely.geometry import Polygon
import numpy as np

logger = logging.getLogger(__name__)


class GoogleEarthEngineService:
    """Service for interacting with Google Earth Engine API"""
    
    def __init__(self):
        self.initialized = False
        self._initialize_ee()
    
    def _initialize_ee(self):
        """Initialize Google Earth Engine"""
        try:
            # Check if already initialized
            try:
                ee.Number(1).getInfo()  # Test if EE is working
                self.initialized = True
                logger.info("Google Earth Engine already initialized")
                return
            except:
                pass  # Not initialized, continue with initialization
            
            # Try to authenticate and initialize
            if settings.GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH:
                import os
                credentials_path = os.path.join(settings.BASE_DIR, settings.GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH)
                if os.path.exists(credentials_path):
                    ee.Authenticate()
                else:
                    logger.warning(f"Credentials file not found at {credentials_path}")
            
            ee.Initialize()
            self.initialized = True
            logger.info("Google Earth Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Earth Engine: {e}")
            self.initialized = False
    
    def get_vegetation_indices(self, image: ee.Image) -> Dict[str, ee.Image]:
        """Calculate various vegetation indices from a satellite image"""
        if not self.initialized:
            raise Exception("Google Earth Engine not initialized")
        
        # Get bands
        nir = image.select('B8')  # Near Infrared
        red = image.select('B4')  # Red
        green = image.select('B3')  # Green
        blue = image.select('B2')  # Blue
        swir1 = image.select('B11')  # Short Wave Infrared 1
        swir2 = image.select('B12')  # Short Wave Infrared 2
        
        # Calculate vegetation indices
        indices = {}
        
        # NDVI - Normalized Difference Vegetation Index
        indices['NDVI'] = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
        
        # EVI - Enhanced Vegetation Index
        indices['EVI'] = nir.subtract(red).divide(
            nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)
        ).multiply(2.5).rename('EVI')
        
        # SAVI - Soil Adjusted Vegetation Index
        l = 0.5  # Soil brightness correction factor
        indices['SAVI'] = nir.subtract(red).divide(
            nir.add(red).add(l)
        ).multiply(1 + l).rename('SAVI')
        
        # NDMI - Normalized Difference Moisture Index
        indices['NDMI'] = nir.subtract(swir1).divide(nir.add(swir1)).rename('NDMI')
        
        # NBR - Normalized Burn Ratio
        indices['NBR'] = nir.subtract(swir2).divide(nir.add(swir2)).rename('NBR')
        
        # NDWI - Normalized Difference Water Index
        indices['NDWI'] = green.subtract(nir).divide(green.add(nir)).rename('NDWI')
        
        # GNDVI - Green Normalized Difference Vegetation Index
        indices['GNDVI'] = nir.subtract(green).divide(nir.add(green)).rename('GNDVI')
        
        # OSAVI - Optimized Soil Adjusted Vegetation Index
        indices['OSAVI'] = nir.subtract(red).divide(nir.add(red).add(0.16)).multiply(1.16).rename('OSAVI')
        
        return indices
    
    def get_sentinel2_images(self, geometry: ee.Geometry, start_date: str, end_date: str, 
                           cloud_cover_threshold: float = 20) -> ee.ImageCollection:
        """Get Sentinel-2 images for a given geometry and date range"""
        if not self.initialized:
            raise Exception("Google Earth Engine not initialized")
        
        collection = (ee.ImageCollection('COPERNICUS/S2_SR')
                     .filterBounds(geometry)
                     .filterDate(start_date, end_date)
                     .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover_threshold)))
        
        return collection
    
    def get_landsat_images(self, geometry: ee.Geometry, start_date: str, end_date: str,
                          cloud_cover_threshold: float = 20) -> ee.ImageCollection:
        """Get Landsat images for a given geometry and date range"""
        if not self.initialized:
            raise Exception("Google Earth Engine not initialized")
        
        # Use Landsat 8 and 9
        landsat8 = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
                   .filterBounds(geometry)
                   .filterDate(start_date, end_date)
                   .filter(ee.Filter.lt('CLOUD_COVER', cloud_cover_threshold)))
        
        landsat9 = (ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
                   .filterBounds(geometry)
                   .filterDate(start_date, end_date)
                   .filter(ee.Filter.lt('CLOUD_COVER', cloud_cover_threshold)))
        
        return landsat8.merge(landsat9)
    
    def get_modis_images(self, geometry: ee.Geometry, start_date: str, end_date: str) -> ee.ImageCollection:
        """Get MODIS images for a given geometry and date range"""
        if not self.initialized:
            raise Exception("Google Earth Engine not initialized")
        
        collection = (ee.ImageCollection('MODIS/006/MOD13Q1')
                     .filterBounds(geometry)
                     .filterDate(start_date, end_date))
        
        return collection
    
    def calculate_statistics(self, image: ee.Image, geometry: ee.Geometry, 
                           scale: int = 30) -> Dict[str, float]:
        """Calculate statistics for an image within a geometry"""
        if not self.initialized:
            raise Exception("Google Earth Engine not initialized")
        
        # Get the band names
        band_names = image.bandNames().getInfo()
        
        # Calculate statistics
        stats = image.reduceRegion(
            reducer=ee.Reducer.minMax().combine(
                ee.Reducer.mean().combine(
                    ee.Reducer.stdDev().combine(
                        ee.Reducer.count(), '', True
                    ), '', True
                ), '', True
            ),
            geometry=geometry,
            scale=scale,
            maxPixels=1e9
        )
        
        result = stats.getInfo()
        
        # Process results for each band
        statistics = {}
        for band in band_names:
            band_stats = {}
            for stat_type in ['min', 'max', 'mean', 'stdDev', 'count']:
                key = f"{band}_{stat_type}"
                if key in result:
                    band_stats[stat_type] = result[key]
            
            statistics[band] = band_stats
        
        return statistics
    
    def get_image_metadata(self, image: ee.Image) -> Dict:
        """Get metadata for a satellite image"""
        if not self.initialized:
            raise Exception("Google Earth Engine not initialized")
        
        properties = image.propertyNames().getInfo()
        metadata = {}
        
        for prop in properties:
            value = image.get(prop).getInfo()
            metadata[prop] = value
        
        return metadata
    
    def geometry_to_ee(self, geometry: GEOSGeometry) -> ee.Geometry:
        """Convert Django GEOSGeometry to Earth Engine Geometry"""
        if geometry.geom_type == 'Polygon':
            coords = list(geometry.coords[0])
            return ee.Geometry.Polygon(coords)
        elif geometry.geom_type == 'MultiPolygon':
            polygons = []
            for polygon in geometry:
                coords = list(polygon.coords[0])
                polygons.append(coords)
            return ee.Geometry.MultiPolygon(polygons)
        else:
            raise ValueError(f"Unsupported geometry type: {geometry.geom_type}")


class VegetationIndexCalculator:
    """Service for calculating vegetation indices and processing monitoring data"""
    
    def __init__(self):
        self.ee_service = GoogleEarthEngineService()
    
    def process_area_monitoring(self, area_of_interest, vegetation_index_name: str, 
                              start_date: str, end_date: str, satellite: str = 'SENTINEL2') -> List[Dict]:
        """Process monitoring for a specific area and vegetation index"""
        try:
            # Check if Google Earth Engine is available
            if not self.ee_service.initialized:
                logger.warning("Google Earth Engine not initialized, returning mock data")
                return self._generate_mock_data(area_of_interest, vegetation_index_name, start_date, end_date)
            
            # Convert geometry to Earth Engine format
            ee_geometry = self.ee_service.geometry_to_ee(area_of_interest.geometry)
            
            logger.info(f"Processing {vegetation_index_name} for area {area_of_interest.name} from {start_date} to {end_date}")
            
            # Get satellite images based on type
            if satellite == 'SENTINEL2':
                image_collection = self.ee_service.get_sentinel2_images(
                    ee_geometry, start_date, end_date
                )
            elif satellite == 'LANDSAT':
                image_collection = self.ee_service.get_landsat_images(
                    ee_geometry, start_date, end_date
                )
            elif satellite == 'MODIS':
                image_collection = self.ee_service.get_modis_images(
                    ee_geometry, start_date, end_date
                )
            else:
                raise ValueError(f"Unsupported satellite: {satellite}")
            
            # Get image list
            image_list = image_collection.toList(100)  # Limit to 100 images
            
            results = []
            
            for i in range(image_list.size().getInfo()):
                try:
                    image = ee.Image(image_list.get(i))
                    
                    # Get image metadata
                    metadata = self.ee_service.get_image_metadata(image)
                    
                    # Calculate vegetation indices
                    indices = self.ee_service.get_vegetation_indices(image)
                    
                    if vegetation_index_name in indices:
                        index_image = indices[vegetation_index_name]
                        
                        # Calculate statistics
                        stats = self.ee_service.calculate_statistics(
                            index_image, ee_geometry
                        )
                        
                        if vegetation_index_name in stats:
                            band_stats = stats[vegetation_index_name]
                            
                            result = {
                                'image_id': metadata.get('system:id', f'image_{i}'),
                                'acquisition_date': metadata.get('system:time_start', ''),
                                'cloud_cover': metadata.get('CLOUDY_PIXEL_PERCENTAGE', 0),
                                'mean_value': band_stats.get('mean', 0),
                                'min_value': band_stats.get('min', 0),
                                'max_value': band_stats.get('max', 0),
                                'std_value': band_stats.get('stdDev', 0),
                                'pixel_count': band_stats.get('count', 0),
                                'metadata': metadata
                            }
                            
                            results.append(result)
                
                except Exception as e:
                    logger.error(f"Error processing image {i}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing area monitoring: {e}")
            # Return mock data as fallback
            return self._generate_mock_data(area_of_interest, vegetation_index_name, start_date, end_date)
    
    def create_monitoring_visualization(self, area_of_interest, vegetation_index_name: str,
                                      start_date: str, end_date: str, satellite: str = 'SENTINEL2') -> str:
        """Create a visualization map for monitoring data"""
        try:
            # Convert geometry to Earth Engine format
            ee_geometry = self.ee_service.geometry_to_ee(area_of_interest.geometry)
            
            # Get the most recent image
            if satellite == 'SENTINEL2':
                image_collection = self.ee_service.get_sentinel2_images(
                    ee_geometry, start_date, end_date
                )
            elif satellite == 'LANDSAT':
                image_collection = self.ee_service.get_landsat_images(
                    ee_geometry, start_date, end_date
                )
            else:
                raise ValueError(f"Unsupported satellite: {satellite}")
            
            # Get the most recent image
            image = image_collection.sort('system:time_start', False).first()
            
            if image is None:
                raise Exception("No images found for the specified criteria")
            
            # Calculate vegetation indices
            indices = self.ee_service.get_vegetation_indices(image)
            
            if vegetation_index_name not in indices:
                raise ValueError(f"Vegetation index {vegetation_index_name} not supported")
            
            index_image = indices[vegetation_index_name]
            
            # Create visualization parameters
            vis_params = {
                'min': -1,
                'max': 1,
                'palette': ['red', 'yellow', 'green']
            }
            
            # Create map
            Map = geemap.Map()
            Map.addLayer(index_image.clip(ee_geometry), vis_params, vegetation_index_name)
            Map.addLayer(ee_geometry, {'color': 'blue'}, 'Area of Interest')
            
            # Center map on area of interest
            bounds = ee_geometry.bounds()
            Map.centerObject(ee_geometry, 12)
            
            # Save map as HTML
            map_html = Map._repr_html_()
            
            return map_html
            
        except Exception as e:
            logger.error(f"Error creating monitoring visualization: {e}")
            raise
    
    def _generate_mock_data(self, area_of_interest, vegetation_index_name: str, 
                           start_date: str, end_date: str) -> List[Dict]:
        """Generate mock monitoring data for testing"""
        import random
        from datetime import datetime, timedelta
        
        # Generate 3-5 mock data points
        num_points = random.randint(3, 5)
        results = []
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        for i in range(num_points):
            # Generate random date within range
            days_diff = (end_dt - start_dt).days
            random_days = random.randint(0, days_diff)
            acquisition_date = start_dt + timedelta(days=random_days)
            
            # Generate mock values based on vegetation index
            if vegetation_index_name == 'NDVI':
                mean_val = random.uniform(0.3, 0.8)
            elif vegetation_index_name == 'EVI':
                mean_val = random.uniform(0.2, 0.6)
            else:
                mean_val = random.uniform(0.1, 0.9)
            
            results.append({
                'image_id': f'mock_SENTINEL2_{i+1}',
                'acquisition_date': acquisition_date.date(),
                'cloud_cover': random.uniform(0, 30),
                'mean_value': round(mean_val, 3),
                'min_value': round(mean_val - 0.1, 3),
                'max_value': round(mean_val + 0.1, 3),
                'std_value': round(random.uniform(0.01, 0.05), 3),
                'pixel_count': random.randint(100, 1000)
            })
        
        return results
    
    def create_realtime_map_visualization(self, area_of_interest, vegetation_index_name: str, 
                                        start_date: str, end_date: str, satellite: str = 'SENTINEL2') -> str:
        """Create a real-time map visualization with actual satellite data"""
        try:
            if not self.ee_service.initialized:
                logger.warning("Google Earth Engine not initialized, cannot create real-time visualization")
                return None
            
            # Convert geometry to Earth Engine format
            ee_geometry = self.ee_service.geometry_to_ee(area_of_interest.geometry)
            
            # Get the most recent image
            if satellite == 'SENTINEL2':
                image_collection = self.ee_service.get_sentinel2_images(ee_geometry, start_date, end_date)
            elif satellite == 'LANDSAT':
                image_collection = self.ee_service.get_landsat_images(ee_geometry, start_date, end_date)
            else:
                image_collection = self.ee_service.get_modis_images(ee_geometry, start_date, end_date)
            
            # Get the most recent image
            recent_image = image_collection.sort('system:time_start', False).first()
            
            # Calculate the vegetation index
            if vegetation_index_name == 'NDVI':
                index_image = self.ee_service.calculate_ndvi(recent_image)
            elif vegetation_index_name == 'EVI':
                index_image = self.ee_service.calculate_evi(recent_image)
            elif vegetation_index_name == 'SAVI':
                index_image = self.ee_service.calculate_savi(recent_image)
            elif vegetation_index_name == 'NDMI':
                index_image = self.ee_service.calculate_ndmi(recent_image)
            elif vegetation_index_name == 'NBR':
                index_image = self.ee_service.calculate_nbr(recent_image)
            elif vegetation_index_name == 'NDWI':
                index_image = self.ee_service.calculate_ndwi(recent_image)
            elif vegetation_index_name == 'GNDVI':
                index_image = self.ee_service.calculate_gndvi(recent_image)
            elif vegetation_index_name == 'OSAVI':
                index_image = self.ee_service.calculate_osavi(recent_image)
            else:
                raise ValueError(f"Unsupported vegetation index: {vegetation_index_name}")
            
            # Create visualization parameters
            vis_params = {
                'min': 0,
                'max': 1,
                'palette': ['red', 'yellow', 'green']
            }
            
            # Create map with geemap if available
            if not GEEMAP_AVAILABLE:
                logger.warning("geemap not available, skipping real-time visualization")
                return None
                
            Map = geemap.Map()
            
            # Add the vegetation index layer
            Map.addLayer(
                index_image.clip(ee_geometry), 
                vis_params, 
                f'{vegetation_index_name} - {satellite}'
            )
            
            # Add the area of interest
            Map.addLayer(
                ee_geometry, 
                {'color': 'blue', 'fillColor': '00000000'}, 
                'Area of Interest'
            )
            
            # Center map on area
            Map.centerObject(ee_geometry, 12)
            
            # Get map as HTML
            map_html = Map._repr_html_()
            
            return map_html
            
        except Exception as e:
            logger.error(f"Error creating real-time map visualization: {e}")
            return None
