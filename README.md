# [AgriInsight - Geospatial Agriculture Data Platform](https://agri-insight.spationex.com)

A comprehensive GIS-based platform for empowering farmers with real-time, data-driven insights into agricultural operations. This system allows users to define farm areas on an interactive map, analyze crop health using satellite-derived vegetation indices from Google Earth Engine, and receive AI-powered recommendations for yield optimization, irrigation, and sustainable practices.

## Features

- **Interactive Map Interface**: Draw and manage farm plots (areas of interest) using Leaflet maps with geospatial precision
- **Vegetation Index Analysis**: Support for multiple vegetation indices (NDVI, EVI, SAVI, NDMI, NBR, NDWI, GNDVI, OSAVI) tailored for crop monitoring
- **Google Earth Engine Integration**: Fetch high-resolution satellite data directly from Google Earth Engine via the GEEMAP API
- **Real-Time Monitoring and AI Insights**: Automated alerts, yield predictions, and personalized recommendations using machine learning
- **Data Visualization**: Interactive charts, dashboards, and exportable reports for historical trends and analytics
- **RESTful API**: Secure, scalable API for data access, integration with third-party tools, and mobile apps
- **PostGIS Database**: Robust spatial database support for geographic queries and data storage
- **Mobile Responsiveness**: Optimized for field use on smartphones and tablets

## Technology Stack

- **Backend**: Django 5.1 with GeoDjango for geospatial capabilities
- **Database**: PostgreSQL with PostGIS extension for spatial data handling
- **Frontend**: HTML5, JavaScript, Leaflet.js, Bootstrap 5 for responsive UI
- **Satellite Data**: Google Earth Engine API for remote sensing
- **Spatial Processing**: GEEMAP, GDAL, GEOS, Geopandas, Rasterio
- **AI/ML**: Scikit-learn and TensorFlow for predictive analytics (e.g., yield forecasting)
- **Task Queue**: Celery with Redis for background processing
- **API**: Django REST Framework with token authentication
- **Visualization**: Matplotlib/Plotly for charts, Folium for embedded maps

## Prerequisites

Before setting up the project, ensure you have the following installed:

1. **Python 3.12+**
2. **PostgreSQL 15+** with PostGIS extension
3. **Redis** (for Celery task queue and caching)
4. **GDAL and GEOS libraries** (for geospatial operations)
5. **Google Earth Engine account** and service account credentials
6. **Node.js** (optional, for frontend build tools like npm for Leaflet plugins)

### Installing GDAL and GEOS

#### Windows
1. Download and install [OSGeo4W](https://trac.osgeo.org/osgeo4w/).
2. Add the `bin` directory to your PATH environment variable.
3. Set library paths (e.g., `GDAL_LIBRARY_PATH` and `GEOS_LIBRARY_PATH`).

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
   git clone https://github.com/ClementNdome/agri_insight.git
   cd agri_insight
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
   cp .env.example .env
   # Edit .env with your configuration (e.g., database credentials, GEE keys)
   ```

5. **Set up PostgreSQL database**
   ```sql
   CREATE DATABASE agri_insight;
   CREATE USER agri_user WITH PASSWORD 'securepassword';
   ALTER ROLE agri_user SET client_encoding TO 'utf8';
   ALTER ROLE agri_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE agri_user SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE agri_insight TO agri_user;
   \c agri_insight
   CREATE EXTENSION postgis;
   ```

6. **Run migrations**
   ```bash
   python manage.py makemigrations
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
   - Visit the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or select an existing one.
   - Enable the Earth Engine API.

2. **Set up authentication**
   - Create a service account and download the JSON credentials file.
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
   - Open your browser and navigate to `http://localhost:8000`.
   - Sign up or log in (supports email verification and social logins via Google).

2. **Define Farm Plots**
   - Navigate to the "Dashboard" tab.
   - Use the "Draw Area" tool to outline farm boundaries on the interactive map.
   - Provide details like crop type and save the area.

3. **Analyze Crop Health**
   - Select a vegetation index (e.g., NDVI for vigor assessment).
   - Specify a date range and satellite source.
   - Click "Analyze" to process data and view results overlaid on the map (styled with color ramps similar to Google Earth Engine).

4. **Monitor and Get Insights**
   - Access the "Monitoring" tab.
   - View historical trends, AI-predicted yields, and recommendations (e.g., irrigation alerts).
   - Export reports in PDF/CSV format.

5. **Set up Alerts**
   - Configure thresholds in the user settings or admin panel.
   - Enable automated notifications via email/SMS for events like drought or pest risks.

### API Usage

The platform offers a secure RESTful API for integration:

#### Areas of Interest (Farm Plots)
```bash
# Get all farm plots
GET /api/areas/

# Create farm plot from GeoJSON
POST /api/areas/create_from_geojson/
{
    "name": "My Corn Field",
    "description": "Primary crop monitoring area",
    "crop_type": "corn",
    "geometry_geojson": {
        "type": "Polygon",
        "coordinates": [[[lon1, lat1], [lon2, lat2], ...]]
    }
}

# Get monitoring data for a farm plot
GET /api/areas/{id}/monitoring_data/?vegetation_index=NDVI&start_date=2025-01-01&end_date=2025-12-31
```

#### Monitoring Data
```bash
# Calculate monitoring data
POST /api/monitoring-data/calculate/
{
    "area_of_interest_id": 1,
    "vegetation_index_name": "NDVI",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
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

The platform supports key indices for agricultural analysis:

- **NDVI**: Normalized Difference Vegetation Index (crop vigor)
- **EVI**: Enhanced Vegetation Index (improved sensitivity in high biomass)
- **SAVI**: Soil Adjusted Vegetation Index (minimizes soil brightness)
- **NDMI**: Normalized Difference Moisture Index (moisture stress detection)
- **NBR**: Normalized Burn Ratio (post-fire or stress assessment)
- **NDWI**: Normalized Difference Water Index (water content in vegetation)
- **GNDVI**: Green Normalized Difference Vegetation Index (chlorophyll estimation)
- **OSAVI**: Optimized Soil Adjusted Vegetation Index (canopy structure)

## Automated Monitoring

Enable background processing with Celery:

1. **Start Redis server**
   ```bash
   redis-server
   ```

2. **Start Celery worker**
   ```bash
   celery -A agri_insight worker -l info
   ```

3. **Process monitoring data**
   ```bash
   python manage.py process_monitoring --days-back 30
   ```

## Configuration

### Monitoring Configuration

Customize parameters per farm plot and index:

- **Monitoring Frequency**: Daily/weekly checks for new satellite data
- **Alert Thresholds**: Low/high values for crop health alerts
- **Change Detection**: Percentage change for anomaly detection (e.g., sudden yield drop)
- **Cloud Cover Threshold**: Max acceptable cloud in images (default: 20%)
- **Minimum Pixel Count**: Ensure sufficient data for accurate analysis

### Alert Types

- **Threshold Low**: Below optimal crop health (e.g., drought indicator)
- **Threshold High**: Above normal (e.g., overgrowth or flooding)
- **Change Detected**: Significant variance from prior data (e.g., pest infestation)
- **Anomaly**: AI-detected outliers (e.g., irregular soil moisture)

## Development

### Running Tests
```bash
pytest
```

### Code Style and Linting
```bash
# Install pre-commit hooks
pre-commit install

# Run linting and formatting
flake8 .
black .
mypy .
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

### Heroku/AWS Deployment (Recommended for Scalability)

1. Configure `Procfile`: `web: gunicorn agri_insight.wsgi --bind 0.0.0.0:$PORT --workers 4`.
2. Set buildpacks: Python, Node.js (if using using frontend builds).
3. Add add-ons: PostgreSQL, Redis.
4. Deploy via Git: `git push heroku main`.
5. Scale: `heroku ps:scale web=1 worker=1`.

### Production Settings

1. Set `DEBUG=False` and `ALLOWED_HOSTS` in `.env`.
2. Use a production database (e.g., AWS RDS).
3. Configure static/media serving with WhiteNoise or S3.
4. Set up email/SMS (e.g., SendGrid/Twilio) for alerts.
5. Enable monitoring with Sentry for error tracking.

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d --build
```

## Troubleshooting

### Common Issues

1. **GDAL/GEOS Library Errors**
   - Confirm installation and environment variables.
   - Test with `gdalinfo --version`.

2. **Google Earth Engine Authentication**
   - Check credentials file permissions and project API enablement.
   - Run `ee.Authenticate()` in shell for verification.

3. **Database Connection Issues**
   - Verify PostgreSQL service status and credentials.
   - Ensure PostGIS is enabled: `SELECT PostGIS_Version();`.

4. **Celery Task Issues**
   - Check Redis connectivity.
   - Review worker logs: `celery -A agri_insight inspect stats`.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/new-feature`).
3. Commit changes (`git commit -m "Add new feature"`).
4. Add tests and ensure they pass.
5. Push and open a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions or issues:
- Open a GitHub issue.
- Consult the documentation.
- Join our community forum (link to be added).

## Acknowledgments

- Google Earth Engine team for satellite data access.
- Django, GeoDjango, and open-source geospatial communities.
- Leaflet.js and mapping library contributors.
- PostgreSQL and PostGIS developers for robust spatial support.

Thank you for using AgriInsight! For collaborations, monetization inquiries, or custom integrations, contact [clementndome20@gmail.com](mailto:clementndome20@gmail.com).