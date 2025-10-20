import json
import logging
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.gis.geos import GEOSGeometry
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    AreaOfInterest, VegetationIndex, SatelliteImage, 
    MonitoringData, MonitoringAlert, MonitoringConfiguration
)
from .serializers import (
    AreaOfInterestSerializer, VegetationIndexSerializer, SatelliteImageSerializer,
    MonitoringDataSerializer, MonitoringAlertSerializer, MonitoringConfigurationSerializer,
    MonitoringDataCreateSerializer, MonitoringVisualizationSerializer, AreaOfInterestCreateSerializer
)
from .services import VegetationIndexCalculator

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class AreaOfInterestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing areas of interest"""
    queryset = AreaOfInterest.objects.all()
    serializer_class = AreaOfInterestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'created_by']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'area_hectares']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter areas by user"""
        if self.request.user.is_authenticated:
            return AreaOfInterest.objects.filter(created_by=self.request.user)
        else:
            # For anonymous users, show all areas or create a default user
            from django.contrib.auth.models import User
            user, created = User.objects.get_or_create(
                username='anonymous',
                defaults={'email': 'anonymous@example.com'}
            )
            return AreaOfInterest.objects.filter(created_by=user)
    
    @action(detail=False, methods=['post'])
    def create_from_geojson(self, request):
        """Create area of interest from GeoJSON"""
        logger.info(f"Received data: {request.data}")
        serializer = AreaOfInterestCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            area = serializer.save()
            return Response(AreaOfInterestSerializer(area).data, status=status.HTTP_201_CREATED)
        logger.error(f"Validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def monitoring_data(self, request, pk=None):
        """Get monitoring data for an area of interest"""
        area = self.get_object()
        monitoring_data = MonitoringData.objects.filter(area_of_interest=area)
        
        # Filter by vegetation index if provided
        vegetation_index = request.query_params.get('vegetation_index')
        if vegetation_index:
            monitoring_data = monitoring_data.filter(vegetation_index__name=vegetation_index)
        
        # Filter by date range if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            monitoring_data = monitoring_data.filter(satellite_image__acquisition_date__gte=start_date)
        if end_date:
            monitoring_data = monitoring_data.filter(satellite_image__acquisition_date__lte=end_date)
        
        serializer = MonitoringDataSerializer(monitoring_data, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def alerts(self, request, pk=None):
        """Get alerts for an area of interest"""
        area = self.get_object()
        alerts = MonitoringAlert.objects.filter(area_of_interest=area)
        
        # Filter by resolved status if provided
        is_resolved = request.query_params.get('is_resolved')
        if is_resolved is not None:
            alerts = alerts.filter(is_resolved=is_resolved.lower() == 'true')
        
        serializer = MonitoringAlertSerializer(alerts, many=True)
        return Response(serializer.data)


class VegetationIndexViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for vegetation indices (read-only)"""
    queryset = VegetationIndex.objects.filter(is_active=True)
    serializer_class = VegetationIndexSerializer
    permission_classes = [IsAuthenticated]


class SatelliteImageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for satellite images (read-only)"""
    queryset = SatelliteImage.objects.all()
    serializer_class = SatelliteImageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['satellite', 'acquisition_date']
    search_fields = ['image_id']
    ordering_fields = ['acquisition_date', 'cloud_cover']
    ordering = ['-acquisition_date']


class MonitoringDataViewSet(viewsets.ModelViewSet):
    """ViewSet for monitoring data"""
    queryset = MonitoringData.objects.all()
    serializer_class = MonitoringDataSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['area_of_interest', 'vegetation_index', 'processing_status']
    search_fields = ['area_of_interest__name', 'vegetation_index__name']
    ordering_fields = ['calculation_date', 'mean_value']
    ordering = ['-calculation_date']
    
    def get_queryset(self):
        """Filter monitoring data by user's areas of interest"""
        user_areas = AreaOfInterest.objects.filter(created_by=self.request.user)
        return MonitoringData.objects.filter(area_of_interest__in=user_areas)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate monitoring data for an area and vegetation index"""
        serializer = MonitoringDataCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            area = AreaOfInterest.objects.get(
                id=data['area_of_interest_id'],
                created_by=request.user
            )
            
            # Get vegetation index
            try:
                vegetation_index = VegetationIndex.objects.get(name=data['vegetation_index_name'])
            except VegetationIndex.DoesNotExist:
                return Response(
                    {'error': f'Vegetation index {data["vegetation_index_name"]} not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate monitoring data
            calculator = VegetationIndexCalculator()
            results = calculator.process_area_monitoring(
                area_of_interest=area,
                vegetation_index_name=data['vegetation_index_name'],
                start_date=data['start_date'].strftime('%Y-%m-%d'),
                end_date=data['end_date'].strftime('%Y-%m-%d'),
                satellite=data['satellite']
            )
            
            # Create monitoring data records
            created_data = []
            for result in results:
                # Create or get satellite image
                satellite_image, created = SatelliteImage.objects.get_or_create(
                    image_id=result['image_id'],
                    defaults={
                        'satellite': data['satellite'],
                        'acquisition_date': result['acquisition_date'],
                        'cloud_cover': result['cloud_cover'],
                        'resolution': 30,  # Default resolution
                        'bounds': area.geometry  # Use area geometry as bounds
                    }
                )
                
                # Create monitoring data
                monitoring_data, created = MonitoringData.objects.get_or_create(
                    area_of_interest=area,
                    vegetation_index=vegetation_index,
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
                    created_data.append(MonitoringDataSerializer(monitoring_data).data)
            
            # Create real-time map visualization
            map_html = calculator.create_realtime_map_visualization(
                area_of_interest=area,
                vegetation_index_name=data['vegetation_index_name'],
                start_date=data['start_date'].strftime('%Y-%m-%d'),
                end_date=data['end_date'].strftime('%Y-%m-%d'),
                satellite=data['satellite']
            )
            
            return Response({
                'message': f'Processed {len(created_data)} monitoring data records',
                'data': created_data,
                'map_html': map_html
            }, status=status.HTTP_201_CREATED)
            
        except AreaOfInterest.DoesNotExist:
            return Response(
                {'error': 'Area of interest not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error calculating monitoring data: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics for monitoring data"""
        queryset = self.get_queryset()
        
        # Filter by area if provided
        area_id = request.query_params.get('area_id')
        if area_id:
            queryset = queryset.filter(area_of_interest_id=area_id)
        
        # Filter by vegetation index if provided
        vegetation_index = request.query_params.get('vegetation_index')
        if vegetation_index:
            queryset = queryset.filter(vegetation_index__name=vegetation_index)
        
        # Calculate statistics
        stats = {}
        for data in queryset:
            index_name = data.vegetation_index.name
            if index_name not in stats:
                stats[index_name] = {
                    'count': 0,
                    'mean_values': [],
                    'min_values': [],
                    'max_values': [],
                    'std_values': []
                }
            
            stats[index_name]['count'] += 1
            stats[index_name]['mean_values'].append(data.mean_value)
            stats[index_name]['min_values'].append(data.min_value)
            stats[index_name]['max_values'].append(data.max_value)
            stats[index_name]['std_values'].append(data.std_value)
        
        # Calculate summary statistics
        summary = {}
        for index_name, data in stats.items():
            summary[index_name] = {
                'count': data['count'],
                'mean_of_means': sum(data['mean_values']) / len(data['mean_values']),
                'min_of_mins': min(data['min_values']),
                'max_of_maxs': max(data['max_values']),
                'avg_std': sum(data['std_values']) / len(data['std_values'])
            }
        
        return Response(summary)


class MonitoringAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for monitoring alerts"""
    queryset = MonitoringAlert.objects.all()
    serializer_class = MonitoringAlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['alert_type', 'severity', 'is_resolved', 'vegetation_index']
    search_fields = ['area_of_interest__name', 'message']
    ordering_fields = ['created_at', 'severity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter alerts by user's areas of interest"""
        user_areas = AreaOfInterest.objects.filter(created_by=self.request.user)
        return MonitoringAlert.objects.filter(area_of_interest__in=user_areas)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark an alert as resolved"""
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = datetime.now()
        alert.save()
        
        return Response({'message': 'Alert resolved successfully'})
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get alert summary statistics"""
        queryset = self.get_queryset()
        
        summary = {
            'total_alerts': queryset.count(),
            'resolved_alerts': queryset.filter(is_resolved=True).count(),
            'unresolved_alerts': queryset.filter(is_resolved=False).count(),
            'by_type': {},
            'by_severity': {}
        }
        
        # Count by alert type
        for alert_type, _ in MonitoringAlert.ALERT_TYPES:
            count = queryset.filter(alert_type=alert_type).count()
            summary['by_type'][alert_type] = count
        
        # Count by severity
        for severity, _ in MonitoringAlert._meta.get_field('severity').choices:
            count = queryset.filter(severity=severity).count()
            summary['by_severity'][severity] = count
        
        return Response(summary)


class MonitoringConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for monitoring configurations"""
    queryset = MonitoringConfiguration.objects.all()
    serializer_class = MonitoringConfigurationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_enabled', 'vegetation_index']
    search_fields = ['area_of_interest__name', 'vegetation_index__name']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Filter configurations by user's areas of interest"""
        user_areas = AreaOfInterest.objects.filter(created_by=self.request.user)
        return MonitoringConfiguration.objects.filter(area_of_interest__in=user_areas)


def index_view(request):
    """Main dashboard view"""
    return render(request, 'index.html')
