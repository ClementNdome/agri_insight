from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from monitoring.models import AreaOfInterest, MonitoringConfiguration, MonitoringData
from monitoring.services import VegetationIndexCalculator


class Command(BaseCommand):
    help = 'Process monitoring data for all configured areas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--area-id',
            type=int,
            help='Process only specific area of interest ID'
        )
        parser.add_argument(
            '--vegetation-index',
            type=str,
            help='Process only specific vegetation index'
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=30,
            help='Number of days back to process (default: 30)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force processing even if data already exists'
        )
    
    def handle(self, *args, **options):
        """Process monitoring data"""
        
        # Get configurations to process
        configurations = MonitoringConfiguration.objects.filter(is_enabled=True)
        
        if options['area_id']:
            configurations = configurations.filter(area_of_interest_id=options['area_id'])
        
        if options['vegetation_index']:
            configurations = configurations.filter(vegetation_index__name=options['vegetation_index'])
        
        if not configurations.exists():
            self.stdout.write(
                self.style.WARNING('No configurations found to process')
            )
            return
        
        # Calculate date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=options['days_back'])
        
        self.stdout.write(
            f'Processing monitoring data from {start_date} to {end_date}'
        )
        
        calculator = VegetationIndexCalculator()
        processed_count = 0
        error_count = 0
        
        for config in configurations:
            try:
                self.stdout.write(
                    f'Processing {config.area_of_interest.name} - {config.vegetation_index.name}'
                )
                
                # Check if data already exists for this period
                if not options['force']:
                    existing_data = MonitoringData.objects.filter(
                        area_of_interest=config.area_of_interest,
                        vegetation_index=config.vegetation_index,
                        satellite_image__acquisition_date__range=[start_date, end_date]
                    ).exists()
                    
                    if existing_data:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Data already exists for {config.area_of_interest.name} - {config.vegetation_index.name}'
                            )
                        )
                        continue
                
                # Process monitoring data
                results = calculator.process_area_monitoring(
                    area=config.area_of_interest,
                    vegetation_index_name=config.vegetation_index.name,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    satellite='SENTINEL2'  # Default to Sentinel-2
                )
                
                # Create monitoring data records
                for result in results:
                    # Create or get satellite image
                    from monitoring.models import SatelliteImage
                    satellite_image, created = SatelliteImage.objects.get_or_create(
                        image_id=result['image_id'],
                        defaults={
                            'satellite': 'SENTINEL2',
                            'acquisition_date': result['acquisition_date'],
                            'cloud_cover': result['cloud_cover'],
                            'resolution': 30,
                            'bounds': config.area_of_interest.geometry
                        }
                    )
                    
                    # Create monitoring data
                    monitoring_data, created = MonitoringData.objects.get_or_create(
                        area_of_interest=config.area_of_interest,
                        vegetation_index=config.vegetation_index,
                        satellite_image=satellite_image,
                        defaults={
                            'mean_value': result['mean_value'],
                            'min_value': result['min_value'],
                            'max_value': result['max_value'],
                            'std_value': result['std_value'],
                            'pixel_count': result['pixel_count'],
                            'processing_status': 'COMPLETED'
                        }
                    )
                    
                    if created:
                        processed_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully processed {len(results)} records for {config.area_of_interest.name} - {config.vegetation_index.name}'
                    )
                )
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing {config.area_of_interest.name} - {config.vegetation_index.name}: {e}'
                    )
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Processing complete. Processed: {processed_count}, Errors: {error_count}'
            )
        )
