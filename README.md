# Forest Monitoring System

A comprehensive GIS system for monitoring forest areas using vegetation indices from Google Earth Engine. This system allows users to draw areas of interest on a map and analyze vegetation health using various satellite-derived indices.

## Features

- **Interactive Map Interface**: Draw and manage areas of interest using Leaflet maps
- **Vegetation Index Analysis**: Support for multiple vegetation indices (NDVI, EVI, SAVI, NDMI, NBR, NDWI, GNDVI, OSAVI)
- **Google Earth Engine Integration**: Pull satellite data directly from Google Earth Engine using the GEEMAP API
- **Real-time Monitoring**: Set up automated monitoring with configurable thresholds and alerts
- **Data Visualization**: Charts and graphs for monitoring data analysis
- **RESTful API**: Complete API for data access and integration
- **PostGIS Database**: Spatial database support for geographic data

## Technology Stack

- **Backend**: Django 4.2 with GeoDjango
- **Database**: PostgreSQL with PostGIS extension
- **Frontend**: HTML5, JavaScript, Leaflet, Bootstrap 5
- **Satellite Data**: Google Earth Engine API
- **Spatial Processing**: GEEMAP, GDAL, GEOS
- **Task Queue**: Celery with Redis
- **API**: Django REST Framework

## Prerequisites

Before setting up the project, ensure you have the following installed:

1. **Python 3.8+**
2. **PostgreSQL 12+** with PostGIS extension
3. **Redis** (for Celery task queue)
4. **GDAL and GEOS libraries**
5. **Google Earth Engine account** and credentials

### Installing GDAL and GEOS

#### Windows
1. Download and install [OSGeo4W](https://trac.osgeo.org/osgeo4w/)
2. Add the bin directory to your PATH
3. Set the library paths in your environment variables

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install gdal-bin libgdal-dev libgeos-dev
```

#### macOS
```bash
brew install gdal geos
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd forest-monitoring-system
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Set up PostgreSQL database**
   ```sql
   CREATE DATABASE forest_monitoring;
   CREATE EXTENSION postgis;
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Initialize vegetation indices**
   ```bash
   python manage.py init_vegetation_indices
   ```

8. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

9. **Start the development server**
   ```bash
   python manage.py runserver
   ```

## Google Earth Engine Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Earth Engine API

2. **Set up authentication**
   - Download your service account credentials JSON file
   - Set the path in your `.env` file:
     ```
     GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH=/path/to/your/credentials.json
     GOOGLE_EARTH_ENGINE_PROJECT=your-project-id
     ```

3. **Authenticate with Earth Engine**
   ```bash
   python manage.py shell
   >>> import ee
   >>> ee.Authenticate()
   >>> ee.Initialize()
   ```

## Usage

### Web Interface

1. **Access the application**
   - Open your browser and go to `http://localhost:8000`
   - Log in with your superuser credentials

2. **Create Areas of Interest**
   - Click on the "Map" tab
   - Use the "Draw Area" button to draw polygons on the map
   - Fill in the area details and save

3. **Analyze Vegetation**
   - Select a vegetation index from the dropdown
   - Choose a date range
   - Click "Analyze Area" to process the data

4. **Monitor Areas**
   - Switch to the "Monitoring" tab
   - Select an area and vegetation index
   - View historical data and trends

5. **Set up Alerts**
   - Configure monitoring thresholds in the admin panel
   - Set up automated monitoring schedules

### API Usage

The system provides a RESTful API for programmatic access:

#### Areas of Interest
```bash
# Get all areas
GET /api/areas/

# Create area from GeoJSON
POST /api/areas/create_from_geojson/
{
    "name": "My Forest Area",
    "description": "A forest monitoring area",
    "geometry_geojson": {
        "type": "Polygon",
        "coordinates": [[[lon1, lat1], [lon2, lat2], ...]]
    }
}

# Get monitoring data for an area
GET /api/areas/{id}/monitoring_data/?vegetation_index=NDVI&start_date=2023-01-01&end_date=2023-12-31
```

#### Monitoring Data
```bash
# Calculate monitoring data
POST /api/monitoring-data/calculate/
{
    "area_of_interest_id": 1,
    "vegetation_index_name": "NDVI",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "satellite": "SENTINEL2"
}

# Get monitoring statistics
GET /api/monitoring-data/statistics/?area_id=1&vegetation_index=NDVI
```

#### Alerts
```bash
# Get all alerts
GET /api/alerts/

# Resolve an alert
POST /api/alerts/{id}/resolve/
```

## Vegetation Indices

The system supports the following vegetation indices:

- **NDVI**: Normalized Difference Vegetation Index
- **EVI**: Enhanced Vegetation Index
- **SAVI**: Soil Adjusted Vegetation Index
- **NDMI**: Normalized Difference Moisture Index
- **NBR**: Normalized Burn Ratio
- **NDWI**: Normalized Difference Water Index
- **GNDVI**: Green Normalized Difference Vegetation Index
- **OSAVI**: Optimized Soil Adjusted Vegetation Index

## Automated Monitoring

Set up automated monitoring using Celery:

1. **Start Redis server**
   ```bash
   redis-server
   ```

2. **Start Celery worker**
   ```bash
   celery -A forest_monitoring worker -l info
   ```

3. **Process monitoring data**
   ```bash
   python manage.py process_monitoring --days-back 30
   ```

## Configuration

### Monitoring Configuration

Configure monitoring parameters for each area and vegetation index combination:

- **Monitoring Frequency**: How often to check for new data
- **Alert Thresholds**: Low and high thresholds for alerts
- **Change Detection**: Percentage change threshold for alerts
- **Cloud Cover Threshold**: Maximum cloud cover to use images
- **Minimum Pixel Count**: Minimum pixels required for analysis

### Alert Types

- **Threshold Low**: Value below low threshold
- **Threshold High**: Value above high threshold
- **Change Detected**: Significant change from previous measurement
- **Anomaly**: Statistical anomaly detected

## Development

### Running Tests
```bash
python manage.py test
```

### Code Style
```bash
# Install pre-commit hooks
pre-commit install

# Run linting
flake8 .
black .
```

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development only)
python manage.py flush
```

## Deployment

### Production Settings

1. **Set DEBUG=False**
2. **Configure proper database settings**
3. **Set up static file serving**
4. **Configure email settings for alerts**
5. **Set up monitoring and logging**

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d
```

## Troubleshooting

### Common Issues

1. **GDAL/GEOS Library Errors**
   - Ensure GDAL and GEOS are properly installed
   - Check library paths in environment variables

2. **Google Earth Engine Authentication**
   - Verify credentials file path
   - Check project ID configuration
   - Ensure Earth Engine API is enabled

3. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check database credentials
   - Ensure PostGIS extension is installed

4. **Celery Task Issues**
   - Verify Redis is running
   - Check Celery worker logs
   - Ensure task imports are correct

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting section

## Acknowledgments

- Google Earth Engine team for providing satellite data access
- Django and GeoDjango communities
- Leaflet and other open-source mapping libraries
- PostGIS and PostgreSQL communities
