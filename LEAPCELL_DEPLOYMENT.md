# Leapcell.io Deployment Guide

This guide will help you deploy the Forest Monitoring System to Leapcell.io.

## Prerequisites

1. A Leapcell.io account (sign up at https://leapcell.io)
2. A PostgreSQL database with PostGIS extension (you can use Leapcell's database service or an external provider)
3. Google Earth Engine credentials (if using Google Earth Engine features)

## Quick Start

### 1. Connect Your Repository

1. Log in to [Leapcell.io](https://leapcell.io)
2. Click "+New Build" or "Create Service"
3. Connect your GitHub/GitLab repository
4. Select the repository containing this project

### 2. Configure Build Settings

**Build Command:**
```bash
pip install --upgrade pip && pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start Command:**
```bash
gunicorn forest_monitoring.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 2 --timeout 120 --access-logfile - --error-logfile -
```

**Port:** Leapcell will automatically set the `PORT` environment variable. Your application should listen on this port.

### 3. Set Environment Variables

In the Leapcell dashboard, configure the following environment variables:

#### Required Variables

- **SECRET_KEY**: Django secret key (generate a new one for production)
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

- **DEBUG**: Set to `False` for production
  ```
  DEBUG=False
  ```

- **ALLOWED_HOSTS**: Comma-separated list of allowed hosts
  ```
  ALLOWED_HOSTS=yourproject.leapcell.dev,www.yourdomain.com
  ```

#### Database Configuration

Choose one of the following options:

**Option 1: Using DATABASE_URL (Recommended)**
```
DATABASE_URL=postgresql://user:password@host:port/dbname
```

**Option 2: Using Individual Database Variables**
```
DB_NAME=forest_monitoring
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=your_db_host
DB_PORT=5432
```

#### GeoDjango Library Paths (Linux)

For Linux deployment, set these paths:
```
GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so
GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so
```

#### Google Earth Engine (Optional)

If using Google Earth Engine:
```
GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_EARTH_ENGINE_PROJECT=your-project-id
```

**Note:** You'll need to upload the credentials JSON file to your deployment and set the path.

#### Redis/Celery (Optional)

If using Celery for background tasks:
```
REDIS_URL=redis://your-redis-host:6379/0
```

#### Other Optional Variables

```
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Twilio (for SMS alerts)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

### 4. Database Setup

Before deploying, you need to:

1. **Create the database** with PostGIS extension:
   ```sql
   CREATE DATABASE forest_monitoring;
   \c forest_monitoring
   CREATE EXTENSION postgis;
   ```

2. **Run migrations** (can be done via build command or after deployment):
   ```bash
   python manage.py migrate
   ```

3. **Initialize vegetation indices**:
   ```bash
   python manage.py init_vegetation_indices
   ```

4. **Create a superuser** (after first deployment):
   ```bash
   python manage.py createsuperuser
   ```

### 5. Pre-Deployment Checklist

- [ ] All environment variables are set
- [ ] DEBUG is set to False
- [ ] SECRET_KEY is generated and secure
- [ ] Database is created with PostGIS extension
- [ ] ALLOWED_HOSTS includes your deployment domain
- [ ] GDAL/GEOS library paths are set for Linux
- [ ] Static files will be collected during build

### 6. Deploy

1. Click "Deploy" in the Leapcell dashboard
2. Monitor the build logs
3. Once deployed, your application will be available at `https://yourproject.leapcell.dev`

### 7. Post-Deployment Steps

1. **Run migrations** (if not included in build command):
   ```bash
   python manage.py migrate
   ```

2. **Collect static files** (should be done in build command):
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Initialize vegetation indices**:
   ```bash
   python manage.py init_vegetation_indices
   ```

4. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

### 8. Continuous Deployment

Leapcell supports automatic deployments via Git:

1. Connect your repository to Leapcell
2. Enable automatic deployments in settings
3. Push to your main branch to trigger deployment
4. Optional: Configure branch protection and deployment approvals

## Configuration Files

The project includes the following deployment files:

- **Procfile**: Contains the gunicorn start command
- **leapcell.yml**: Deployment configuration (optional)
- **requirements.txt**: Python dependencies

## Troubleshooting

### Common Issues

1. **Static files not loading**
   - Ensure `collectstatic` runs during build
   - Check STATIC_ROOT and STATIC_URL settings
   - Verify whitenoise is properly configured

2. **Database connection errors**
   - Verify database credentials
   - Check if PostGIS extension is installed
   - Ensure database host is accessible from Leapcell

3. **GDAL/GEOS errors**
   - Verify library paths are correct for Linux
   - Check if GDAL libraries are installed in the container
   - May need to add system dependencies to build

4. **ALLOWED_HOSTS errors**
   - Add your domain to ALLOWED_HOSTS environment variable
   - Check the exact domain name (with or without www)

5. **Port binding issues**
   - Ensure gunicorn binds to `0.0.0.0:${PORT}`
   - Check that PORT environment variable is set

### Getting Help

- Check Leapcell.io documentation: https://docs.leapcell.io
- Join Leapcell Discord community
- Contact support: support@leapcell.io

## Production Recommendations

1. **Security**
   - Never commit `.env` files or credentials
   - Use strong SECRET_KEY
   - Enable HTTPS (handled by Leapcell)
   - Set DEBUG=False
   - Review CORS and CSRF settings

2. **Performance**
   - Use database connection pooling
   - Enable caching (Redis recommended)
   - Optimize static file serving with whitenoise
   - Consider CDN for static assets

3. **Monitoring**
   - Set up error tracking (Sentry, etc.)
   - Monitor application logs
   - Track database performance
   - Monitor Celery tasks if used

4. **Database**
   - Use managed database service
   - Set up regular backups
   - Monitor database performance
   - Consider read replicas for scaling

## Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [GeoDjango Installation](https://docs.djangoproject.com/en/stable/ref/contrib/gis/install/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [WhiteNoise Documentation](http://whitenoise.evans.io/)

