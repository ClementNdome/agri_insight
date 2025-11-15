FROM python:3.12-slim

# Install system deps for GDAL/rasterio
RUN apt-get update && apt-get install -y \
    libgdal-dev gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# Set work dir
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static (runtime)
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE $PORT

# Start command (overridden in dashboard)
CMD ["gunicorn", "agri_insight.wsgi:application", "--bind", "0.0.0.0:$PORT", "--workers", "2", "--threads", "2", "--timeout", "120"]