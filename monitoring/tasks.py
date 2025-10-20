from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .models import MonitoringConfiguration, MonitoringData, MonitoringAlert
from .services import VegetationIndexCalculator

logger = logging.getLogger(__name__)


@shared_task
def process_monitoring_data(area_id=None, vegetation_index_name=None, days_back=30):
    """
    Process monitoring data for configured areas
    """
    try:
        # Get configurations to process
        configurations = MonitoringConfiguration.objects.filter(is_enabled=True)
        
        if area_id:
            configurations = configurations.filter(area_of_interest_id=area_id)
        
        if vegetation_index_name:
            configurations = configurations.filter(vegetation_index__name=vegetation_index_name)
        
        if not configurations.exists():
            logger.warning('No configurations found to process')
            return {'status': 'no_configurations', 'processed': 0}
        
        # Calculate date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        calculator = VegetationIndexCalculator()
        processed_count = 0
        error_count = 0
        
        for config in configurations:
            try:
                logger.info(f'Processing {config.area_of_interest.name} - {config.vegetation_index.name}')
                
                # Process monitoring data
                results = calculator.process_area_monitoring(
                    area=config.area_of_interest,
                    vegetation_index_name=config.vegetation_index.name,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    satellite='SENTINEL2'
                )
                
                # Create monitoring data records
                for result in results:
                    from .models import SatelliteImage
                    
                    # Create or get satellite image
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
                        
                        # Check for alerts
                        check_alerts.delay(monitoring_data.id)
                
                logger.info(f'Successfully processed {len(results)} records for {config.area_of_interest.name}')
                
            except Exception as e:
                error_count += 1
                logger.error(f'Error processing {config.area_of_interest.name}: {e}')
                continue
        
        return {
            'status': 'completed',
            'processed': processed_count,
            'errors': error_count
        }
        
    except Exception as e:
        logger.error(f'Error in process_monitoring_data task: {e}')
        return {'status': 'error', 'error': str(e)}


@shared_task
def check_alerts(monitoring_data_id):
    """
    Check for alerts based on monitoring data
    """
    try:
        monitoring_data = MonitoringData.objects.get(id=monitoring_data_id)
        config = MonitoringConfiguration.objects.get(
            area_of_interest=monitoring_data.area_of_interest,
            vegetation_index=monitoring_data.vegetation_index
        )
        
        alerts_created = []
        
        # Check low threshold
        if config.low_threshold is not None and monitoring_data.mean_value < config.low_threshold:
            alert = MonitoringAlert.objects.create(
                area_of_interest=monitoring_data.area_of_interest,
                vegetation_index=monitoring_data.vegetation_index,
                monitoring_data=monitoring_data,
                alert_type='THRESHOLD_LOW',
                message=f'Value {monitoring_data.mean_value:.4f} is below low threshold {config.low_threshold}',
                threshold_value=config.low_threshold,
                actual_value=monitoring_data.mean_value,
                severity='MEDIUM'
            )
            alerts_created.append(alert.id)
        
        # Check high threshold
        if config.high_threshold is not None and monitoring_data.mean_value > config.high_threshold:
            alert = MonitoringAlert.objects.create(
                area_of_interest=monitoring_data.area_of_interest,
                vegetation_index=monitoring_data.vegetation_index,
                monitoring_data=monitoring_data,
                alert_type='THRESHOLD_HIGH',
                message=f'Value {monitoring_data.mean_value:.4f} is above high threshold {config.high_threshold}',
                threshold_value=config.high_threshold,
                actual_value=monitoring_data.mean_value,
                severity='MEDIUM'
            )
            alerts_created.append(alert.id)
        
        # Check for significant changes
        if config.change_threshold_percent is not None:
            previous_data = MonitoringData.objects.filter(
                area_of_interest=monitoring_data.area_of_interest,
                vegetation_index=monitoring_data.vegetation_index,
                calculation_date__lt=monitoring_data.calculation_date
            ).order_by('-calculation_date').first()
            
            if previous_data:
                change_percent = abs(
                    (monitoring_data.mean_value - previous_data.mean_value) / previous_data.mean_value * 100
                )
                
                if change_percent > config.change_threshold_percent:
                    alert = MonitoringAlert.objects.create(
                        area_of_interest=monitoring_data.area_of_interest,
                        vegetation_index=monitoring_data.vegetation_index,
                        monitoring_data=monitoring_data,
                        alert_type='CHANGE_DETECTED',
                        message=f'Significant change detected: {change_percent:.2f}% change from previous value',
                        threshold_value=config.change_threshold_percent,
                        actual_value=change_percent,
                        severity='HIGH'
                    )
                    alerts_created.append(alert.id)
        
        return {
            'status': 'completed',
            'alerts_created': len(alerts_created),
            'alert_ids': alerts_created
        }
        
    except Exception as e:
        logger.error(f'Error in check_alerts task: {e}')
        return {'status': 'error', 'error': str(e)}


@shared_task
def cleanup_old_data(days_to_keep=365):
    """
    Clean up old monitoring data and alerts
    """
    try:
        cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)
        
        # Delete old monitoring data
        old_data_count = MonitoringData.objects.filter(
            calculation_date__lt=cutoff_date
        ).count()
        
        MonitoringData.objects.filter(
            calculation_date__lt=cutoff_date
        ).delete()
        
        # Delete old resolved alerts
        old_alerts_count = MonitoringAlert.objects.filter(
            is_resolved=True,
            created_at__lt=cutoff_date
        ).count()
        
        MonitoringAlert.objects.filter(
            is_resolved=True,
            created_at__lt=cutoff_date
        ).delete()
        
        return {
            'status': 'completed',
            'deleted_data': old_data_count,
            'deleted_alerts': old_alerts_count
        }
        
    except Exception as e:
        logger.error(f'Error in cleanup_old_data task: {e}')
        return {'status': 'error', 'error': str(e)}
