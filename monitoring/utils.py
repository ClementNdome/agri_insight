import json
import logging
from typing import Dict, List, Optional, Tuple
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import Polygon, MultiPolygon
from shapely.geometry import shape
import numpy as np

logger = logging.getLogger(__name__)


def geojson_to_geos(geojson_data: Dict) -> GEOSGeometry:
    """
    Convert GeoJSON data to Django GEOSGeometry
    
    Args:
        geojson_data: GeoJSON dictionary
        
    Returns:
        GEOSGeometry object
    """
    try:
        # Use shapely to parse GeoJSON
        shapely_geom = shape(geojson_data)
        
        # Convert to GEOSGeometry
        geos_geom = GEOSGeometry(shapely_geom.wkt)
        
        return geos_geom
    except Exception as e:
        logger.error(f"Error converting GeoJSON to GEOSGeometry: {e}")
        raise ValueError(f"Invalid GeoJSON data: {e}")


def geos_to_geojson(geos_geom: GEOSGeometry) -> Dict:
    """
    Convert Django GEOSGeometry to GeoJSON
    
    Args:
        geos_geom: GEOSGeometry object
        
    Returns:
        GeoJSON dictionary
    """
    try:
        return json.loads(geos_geom.geojson)
    except Exception as e:
        logger.error(f"Error converting GEOSGeometry to GeoJSON: {e}")
        raise ValueError(f"Error converting geometry: {e}")


def calculate_polygon_area_hectares(geometry: GEOSGeometry) -> float:
    """
    Calculate polygon area in hectares
    
    Args:
        geometry: GEOSGeometry polygon
        
    Returns:
        Area in hectares
    """
    try:
        if geometry.geom_type in ['Polygon', 'MultiPolygon']:
            # This is a rough approximation for small areas
            # For production, use proper projection
            area_sq_degrees = geometry.area
            # Convert square degrees to hectares (very approximate)
            area_hectares = area_sq_degrees * 10000
            return area_hectares
        else:
            return 0.0
    except Exception as e:
        logger.error(f"Error calculating polygon area: {e}")
        return 0.0


def get_polygon_centroid(geometry: GEOSGeometry) -> Tuple[float, float]:
    """
    Get polygon centroid coordinates
    
    Args:
        geometry: GEOSGeometry polygon
        
    Returns:
        Tuple of (longitude, latitude)
    """
    try:
        centroid = geometry.centroid
        return (centroid.x, centroid.y)
    except Exception as e:
        logger.error(f"Error calculating polygon centroid: {e}")
        return (0.0, 0.0)


def validate_geometry(geometry: GEOSGeometry) -> bool:
    """
    Validate geometry for forest monitoring
    
    Args:
        geometry: GEOSGeometry object
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check if geometry is valid
        if not geometry.valid:
            return False
        
        # Check if it's a polygon or multipolygon
        if geometry.geom_type not in ['Polygon', 'MultiPolygon']:
            return False
        
        # Check if area is reasonable (not too small or too large)
        area_hectares = calculate_polygon_area_hectares(geometry)
        if area_hectares < 0.01:  # Less than 0.01 hectares
            return False
        if area_hectares > 1000000:  # More than 1 million hectares
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error validating geometry: {e}")
        return False


def calculate_vegetation_index_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate statistics for vegetation index values
    
    Args:
        values: List of vegetation index values
        
    Returns:
        Dictionary with statistics
    """
    try:
        if not values:
            return {
                'mean': 0.0,
                'min': 0.0,
                'max': 0.0,
                'std': 0.0,
                'count': 0
            }
        
        values_array = np.array(values)
        
        return {
            'mean': float(np.mean(values_array)),
            'min': float(np.min(values_array)),
            'max': float(np.max(values_array)),
            'std': float(np.std(values_array)),
            'count': len(values)
        }
    except Exception as e:
        logger.error(f"Error calculating vegetation index statistics: {e}")
        return {
            'mean': 0.0,
            'min': 0.0,
            'max': 0.0,
            'std': 0.0,
            'count': 0
        }


def detect_vegetation_anomalies(values: List[float], threshold: float = 2.0) -> List[int]:
    """
    Detect anomalies in vegetation index values using z-score
    
    Args:
        values: List of vegetation index values
        threshold: Z-score threshold for anomaly detection
        
    Returns:
        List of indices where anomalies were detected
    """
    try:
        if len(values) < 3:  # Need at least 3 values for meaningful statistics
            return []
        
        values_array = np.array(values)
        mean = np.mean(values_array)
        std = np.std(values_array)
        
        if std == 0:  # All values are the same
            return []
        
        z_scores = np.abs((values_array - mean) / std)
        anomalies = np.where(z_scores > threshold)[0]
        
        return anomalies.tolist()
    except Exception as e:
        logger.error(f"Error detecting vegetation anomalies: {e}")
        return []


def calculate_vegetation_trend(values: List[float], dates: List[str]) -> Dict[str, float]:
    """
    Calculate vegetation trend over time
    
    Args:
        values: List of vegetation index values
        dates: List of date strings
        
    Returns:
        Dictionary with trend information
    """
    try:
        if len(values) < 2:
            return {
                'trend': 0.0,
                'slope': 0.0,
                'r_squared': 0.0,
                'p_value': 1.0
            }
        
        # Convert dates to numeric values (days since first date)
        from datetime import datetime
        first_date = datetime.strptime(dates[0], '%Y-%m-%d')
        x_values = [(datetime.strptime(date, '%Y-%m-%d') - first_date).days for date in dates]
        
        # Calculate linear regression
        x_array = np.array(x_values)
        y_array = np.array(values)
        
        # Calculate slope and intercept
        n = len(x_array)
        sum_x = np.sum(x_array)
        sum_y = np.sum(y_array)
        sum_xy = np.sum(x_array * y_array)
        sum_x2 = np.sum(x_array ** 2)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n
        
        # Calculate R-squared
        y_pred = slope * x_array + intercept
        ss_res = np.sum((y_array - y_pred) ** 2)
        ss_tot = np.sum((y_array - np.mean(y_array)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine trend direction
        if slope > 0.001:
            trend = 1.0  # Increasing
        elif slope < -0.001:
            trend = -1.0  # Decreasing
        else:
            trend = 0.0  # Stable
        
        return {
            'trend': trend,
            'slope': float(slope),
            'r_squared': float(r_squared),
            'p_value': 0.0  # Simplified - would need proper statistical test
        }
    except Exception as e:
        logger.error(f"Error calculating vegetation trend: {e}")
        return {
            'trend': 0.0,
            'slope': 0.0,
            'r_squared': 0.0,
            'p_value': 1.0
        }


def format_vegetation_index_value(value: float, index_name: str) -> str:
    """
    Format vegetation index value for display
    
    Args:
        value: Vegetation index value
        index_name: Name of the vegetation index
        
    Returns:
        Formatted string
    """
    try:
        # Different indices have different typical ranges
        if index_name in ['NDVI', 'EVI', 'SAVI', 'GNDVI', 'OSAVI']:
            # These typically range from -1 to 1
            return f"{value:.4f}"
        elif index_name in ['NDMI', 'NBR', 'NDWI']:
            # These also typically range from -1 to 1
            return f"{value:.4f}"
        else:
            # Default formatting
            return f"{value:.4f}"
    except Exception as e:
        logger.error(f"Error formatting vegetation index value: {e}")
        return f"{value:.4f}"


def get_vegetation_index_description(index_name: str) -> str:
    """
    Get description for vegetation index
    
    Args:
        index_name: Name of the vegetation index
        
    Returns:
        Description string
    """
    descriptions = {
        'NDVI': 'Normalized Difference Vegetation Index - measures vegetation health and density',
        'EVI': 'Enhanced Vegetation Index - improved version of NDVI with atmospheric correction',
        'SAVI': 'Soil Adjusted Vegetation Index - minimizes soil brightness effects',
        'NDMI': 'Normalized Difference Moisture Index - measures vegetation water content',
        'NBR': 'Normalized Burn Ratio - used for mapping burned areas and fire severity',
        'NDWI': 'Normalized Difference Water Index - measures water content in vegetation',
        'GNDVI': 'Green Normalized Difference Vegetation Index - more sensitive to chlorophyll',
        'OSAVI': 'Optimized Soil Adjusted Vegetation Index - optimized version of SAVI'
    }
    
    return descriptions.get(index_name, 'Vegetation index for forest monitoring')


def get_vegetation_index_range(index_name: str) -> Tuple[float, float]:
    """
    Get typical range for vegetation index
    
    Args:
        index_name: Name of the vegetation index
        
    Returns:
        Tuple of (min_value, max_value)
    """
    ranges = {
        'NDVI': (-1.0, 1.0),
        'EVI': (-1.0, 1.0),
        'SAVI': (-1.0, 1.0),
        'NDMI': (-1.0, 1.0),
        'NBR': (-1.0, 1.0),
        'NDWI': (-1.0, 1.0),
        'GNDVI': (-1.0, 1.0),
        'OSAVI': (-1.0, 1.0)
    }
    
    return ranges.get(index_name, (-1.0, 1.0))
