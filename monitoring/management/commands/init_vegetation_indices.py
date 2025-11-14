from django.core.management.base import BaseCommand
from monitoring.models import VegetationIndex


class Command(BaseCommand):
    help = 'Initialize vegetation indices in the database'
    
    def handle(self, *args, **options):
        """Initialize vegetation indices"""
        
        vegetation_indices = [
            {
                'name': 'NDVI',
                'full_name': 'Normalized Difference Vegetation Index',
                'description': 'Measures vegetation health and density. Values range from -1 to 1, with higher values indicating healthier vegetation.',
                'formula': 'NDVI = (NIR - Red) / (NIR + Red)'
            },
            {
                'name': 'EVI',
                'full_name': 'Enhanced Vegetation Index',
                'description': 'Improved version of NDVI that reduces atmospheric and soil background influences.',
                'formula': 'EVI = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)'
            },
            {
                'name': 'SAVI',
                'full_name': 'Soil Adjusted Vegetation Index',
                'description': 'Minimizes soil brightness effects in vegetation measurements.',
                'formula': 'SAVI = (NIR - Red) / (NIR + Red + L) * (1 + L)'
            },
            {
                'name': 'NDMI',
                'full_name': 'Normalized Difference Moisture Index',
                'description': 'Measures vegetation water content and moisture stress.',
                'formula': 'NDMI = (NIR - SWIR1) / (NIR + SWIR1)'
            },
            {
                'name': 'NBR',
                'full_name': 'Normalized Burn Ratio',
                'description': 'Used for mapping burned areas and fire severity.',
                'formula': 'NBR = (NIR - SWIR2) / (NIR + SWIR2)'
            },
            {
                'name': 'NDWI',
                'full_name': 'Normalized Difference Water Index',
                'description': 'Measures water content in vegetation and water bodies.',
                'formula': 'NDWI = (Green - NIR) / (Green + NIR)'
            },
            {
                'name': 'GNDVI',
                'full_name': 'Green Normalized Difference Vegetation Index',
                'description': 'Uses green band instead of red, more sensitive to chlorophyll content.',
                'formula': 'GNDVI = (NIR - Green) / (NIR + Green)'
            },
            {
                'name': 'OSAVI',
                'full_name': 'Optimized Soil Adjusted Vegetation Index',
                'description': 'Optimized version of SAVI with fixed soil adjustment factor.',
                'formula': 'OSAVI = (NIR - Red) / (NIR + Red + 0.16) * 1.16'
            },
            {
                'name': 'NDRE',
                'full_name': 'Normalized Difference Red Edge',
                'description': 'Uses red edge band (B5) to assess chlorophyll content and vegetation stress. More sensitive to early stress detection than NDVI.',
                'formula': 'NDRE = (NIR - Red Edge) / (NIR + Red Edge)'
            },
            {
                'name': 'CIRE',
                'full_name': 'Chlorophyll Index Red Edge',
                'description': 'Measures chlorophyll content using red edge band. Higher values indicate more chlorophyll.',
                'formula': 'CIRE = (NIR / Red Edge) - 1'
            },
            {
                'name': 'LAI',
                'full_name': 'Leaf Area Index',
                'description': 'Measures the total leaf area per unit ground area. Values typically range from 0 (bare ground) to 6+ (dense canopy).',
                'formula': 'LAI = 3.618 * NDVI - 0.118 (simplified empirical relationship)'
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for index_data in vegetation_indices:
            index, created = VegetationIndex.objects.get_or_create(
                name=index_data['name'],
                defaults=index_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created vegetation index: {index.name}')
                )
            else:
                # Update existing index
                for key, value in index_data.items():
                    setattr(index, key, value)
                index.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated vegetation index: {index.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Vegetation indices initialization complete. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
