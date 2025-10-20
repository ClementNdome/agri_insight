#!/usr/bin/env python
"""
Google Earth Engine Setup Script for Forest Monitoring System
"""

import os
import sys
import json
from pathlib import Path

def check_credentials_file():
    """Check if credentials file exists and is valid"""
    credentials_path = os.getenv('GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH', './ee-clementndome20-6dbfd245d3ee.json')
    
    if not os.path.exists(credentials_path):
        print(f"✗ Credentials file not found at: {credentials_path}")
        print("\nTo get your credentials file:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable the Earth Engine API")
        print("4. Go to IAM & Admin > Service Accounts")
        print("5. Create a new service account")
        print("6. Add 'Earth Engine User' role")
        print("7. Create a JSON key and download it")
        print("8. Save it as 'credentials.json' in your project directory")
        print("9. Update your .env file with the correct path")
        return False
    
    try:
        with open(credentials_path, 'r') as f:
            creds = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds]
        
        if missing_fields:
            print(f"✗ Invalid credentials file. Missing fields: {missing_fields}")
            return False
        
        print(f"✓ Credentials file found and valid: {credentials_path}")
        print(f"  Project ID: {creds.get('project_id', 'Unknown')}")
        print(f"  Service Account: {creds.get('client_email', 'Unknown')}")
        return True
        
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON in credentials file: {credentials_path}")
        return False
    except Exception as e:
        print(f"✗ Error reading credentials file: {e}")
        return False

def test_earth_engine_connection():
    """Test Earth Engine connection"""
    try:
        import ee
        print("Testing Earth Engine connection...")
        
        # Initialize Earth Engine
        ee.Initialize(project='ee-clementndome20')
        
        # Test with a simple operation - get a single image
        test_image = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").first()
        test_geometry = ee.Geometry.Rectangle([0, 0, 1, 1])
        
        # Get some basic info about the image
        image_id = test_image.get('system:id').getInfo()
        print("✓ Earth Engine connection successful!")
        print(f"  Test image ID: {image_id}")
        
        # Test vegetation index calculation
        ndvi = test_image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        print("✓ Successfully calculated NDVI")
        
        return True
        
    except ImportError:
        print("✗ Earth Engine API not installed. Run: pip install earthengine-api")
        return False
    except Exception as e:
        print(f"✗ Earth Engine connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure your credentials file is correct")
        print("2. Verify the project ID in your .env file matches the credentials")
        print("3. Ensure Earth Engine API is enabled in Google Cloud Console")
        print("4. Check that billing is enabled on your Google Cloud project")
        return False

def setup_environment_variables():
    """Help set up environment variables"""
    print("\nEnvironment Variables Setup:")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("✗ .env file not found")
        print("Creating .env file from template...")
        
        if os.path.exists('env.example'):
            import shutil
            shutil.copy('env.example', '.env')
            print("✓ Created .env file from template")
        else:
            print("✗ env.example file not found")
            return False
    
    # Read current .env file
    with open('.env', 'r') as f:
        env_content = f.read()
    
    # Check for required variables
    required_vars = [
        'GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH',
        'GOOGLE_EARTH_ENGINE_PROJECT'
    ]
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=" not in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠ Missing environment variables: {', '.join(missing_vars)}")
        print("\nPlease update your .env file with:")
        print("GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH=./credentials.json")
        print("GOOGLE_EARTH_ENGINE_PROJECT=your-project-id")
        return False
    
    print("✓ Environment variables configured")
    return True

def main():
    """Main setup function"""
    print("Google Earth Engine Setup for Forest Monitoring System")
    print("=" * 60)
    
    # Check environment variables
    if not setup_environment_variables():
        print("\nPlease configure your .env file and run this script again")
        return
    
    # Check credentials file
    if not check_credentials_file():
        print("\nPlease obtain your credentials file and run this script again")
        return
    
    # Test Earth Engine connection
    if not test_earth_engine_connection():
        print("\nPlease fix the connection issues and run this script again")
        return
    
    print("\n" + "=" * 60)
    print("✓ Google Earth Engine setup completed successfully!")
    print("\nYou can now:")
    print("1. Run the Django development server: python manage.py runserver")
    print("2. Access the application at: http://localhost:8000")
    print("3. Start monitoring forest areas with vegetation indices")

if __name__ == '__main__':
    main()
