#!/usr/bin/env python3
"""
Google Earth Engine Authentication Setup Script
This script helps you set up Google Earth Engine authentication for the AgriInsight - Geospatial Agriculture Data Platform.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_ee_installation():
    """Check if earthengine-api is installed"""
    try:
        import ee
        print("✅ Google Earth Engine API is installed")
        return True
    except ImportError:
        print("❌ Google Earth Engine API is not installed")
        print("Installing earthengine-api...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "earthengine-api"])
            print("✅ Google Earth Engine API installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install earthengine-api")
            return False

def authenticate_ee():
    """Authenticate with Google Earth Engine"""
    try:
        import ee
        print("\n🔐 Starting Google Earth Engine authentication...")
        print("This will open your browser for authentication.")
        print("Please follow the instructions to authenticate with your Google account.")
        
        # Authenticate
        ee.Authenticate()
        
        # Initialize
        ee.Initialize()
        
        # Test authentication
        test_result = ee.Number(1).getInfo()
        if test_result == 1:
            print("✅ Google Earth Engine authentication successful!")
            return True
        else:
            print("❌ Authentication test failed")
            return False
            
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

def create_credentials_file():
    """Create a credentials file for the Django app"""
    try:
        # Get the credentials from the default location
        credentials_path = Path.home() / ".config" / "earthengine" / "credentials"
        
        if credentials_path.exists():
            print(f"✅ Found credentials at {credentials_path}")
            
            # Copy to project directory
            project_credentials = Path("gee_credentials.json")
            with open(credentials_path, 'r') as src:
                with open(project_credentials, 'w') as dst:
                    dst.write(src.read())
            
            print(f"✅ Credentials copied to {project_credentials}")
            return True
        else:
            print("❌ No credentials found. Please run authentication first.")
            return False
            
    except Exception as e:
        print(f"❌ Error creating credentials file: {e}")
        return False

def update_env_file():
    """Update .env file with GEE credentials path"""
    env_file = Path(".env")
    
    if env_file.exists():
        # Read existing .env file
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update or add GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH"):
                lines[i] = "GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH=gee_credentials.json\n"
                updated = True
                break
        
        if not updated:
            lines.append("GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH=gee_credentials.json\n")
        
        # Write back to .env file
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print("✅ Updated .env file with GEE credentials path")
    else:
        # Create new .env file
        with open(env_file, 'w') as f:
            f.write("GOOGLE_EARTH_ENGINE_CREDENTIALS_PATH=gee_credentials.json\n")
        
        print("✅ Created .env file with GEE credentials path")

def test_gee_integration():
    """Test GEE integration with the Django app"""
    try:
        print("\n🧪 Testing Google Earth Engine integration...")
        
        # Test basic EE functionality
        import ee
        ee.Initialize(project='ee-clementndome20')
        
        # Test image collection access
        sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR')
        count = sentinel2.size().getInfo()
        print(f"✅ Successfully accessed Sentinel-2 collection ({count} images)")
        
        # Test vegetation index calculation
        test_image = sentinel2.first()
        ndvi = test_image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        print("✅ Successfully calculated NDVI")
        
        print("✅ Google Earth Engine integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ GEE integration test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🌍 Google Earth Engine Setup for AgriInsight - Geospatial Agriculture Data Platform")
    print("=" * 60)
    
   
    if not check_ee_installation():
        return False
    
    # Step 2: Authenticate
    if not authenticate_ee():
        return False
    
    # Step 3: Create credentials file
    if not create_credentials_file():
        return False
    
    # Step 4: Update .env file
    update_env_file()
    
    # Step 5: Test integration
    if not test_gee_integration():
        return False
    
    print("\n🎉 Google Earth Engine setup completed successfully!")
    print("\nNext steps:")
    print("1. Run: python manage.py runserver")
    print("2. Open: http://127.0.0.1:8000")
    print("3. Draw an area and analyze it with real satellite data!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
