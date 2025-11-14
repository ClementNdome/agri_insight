import json
import logging
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.gis.geos import GEOSGeometry
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
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
    MonitoringData, MonitoringAlert, MonitoringConfiguration, Tip
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
    serializer_class = AreaOfInterestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'crop_type']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name', 'area_hectares']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return AreaOfInterest.objects.none()
        return AreaOfInterest.objects.filter(created_by=user)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_from_geojson(self, request):
        """Create an area of interest from GeoJSON geometry"""
        try:
            data = request.data
            geometry_geojson = data.get('geometry_geojson')
            
            if not geometry_geojson:
                return Response(
                    {'error': 'geometry_geojson is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Handle both Feature and Geometry objects
            # Leaflet's toGeoJSON() returns a Feature object with geometry property
            if isinstance(geometry_geojson, dict):
                if geometry_geojson.get('type') == 'Feature':
                    # Extract geometry from Feature object
                    geometry_data = geometry_geojson.get('geometry')
                    if not geometry_data:
                        return Response(
                            {'error': 'Feature object must contain a geometry property'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                elif geometry_geojson.get('type') in ['Polygon', 'MultiPolygon', 'Point', 'LineString', 'MultiLineString', 'MultiPoint']:
                    # It's already a geometry object
                    geometry_data = geometry_geojson
                else:
                    return Response(
                        {'error': 'Invalid GeoJSON format. Expected Feature or Geometry object'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'error': 'geometry_geojson must be a dictionary'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert GeoJSON geometry to GEOS geometry
            try:
                geometry = GEOSGeometry(json.dumps(geometry_data))
            except Exception as geos_error:
                logger.error(f"GEOSGeometry conversion error: {str(geos_error)}")
                # Try using the utility function as fallback
                try:
                    from .utils import geojson_to_geos
                    geometry = geojson_to_geos(geometry_data)
                except Exception as util_error:
                    logger.error(f"Utility function error: {str(util_error)}")
                    return Response(
                        {'error': f'Invalid geometry: {str(geos_error)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Validate geometry type
            if geometry.geom_type not in ['Polygon', 'MultiPolygon']:
                return Response(
                    {'error': f'Geometry must be a Polygon or MultiPolygon, got {geometry.geom_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create area
            area = AreaOfInterest.objects.create(
                name=data.get('name', 'Unnamed Area'),
                description=data.get('description', ''),
                geometry=geometry,
                created_by=request.user
            )
            
            serializer = AreaOfInterestSerializer(area)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating area from GeoJSON: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def monitoring_data(self, request, pk=None):
        """Get monitoring data for a specific area"""
        area = self.get_object()
        vegetation_index = request.query_params.get('vegetation_index')
        
        queryset = MonitoringData.objects.filter(area_of_interest=area)
        
        if vegetation_index:
            queryset = queryset.filter(vegetation_index__name=vegetation_index)
        
        serializer = MonitoringDataSerializer(queryset, many=True)
        return Response(serializer.data)


class VegetationIndexViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing vegetation indices"""
    queryset = VegetationIndex.objects.filter(is_active=True)
    serializer_class = VegetationIndexSerializer
    permission_classes = []  # Allow public access
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'full_name', 'description']
    ordering_fields = ['name', 'full_name']
    ordering = ['name']


class SatelliteImageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing satellite images"""
    serializer_class = SatelliteImageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['satellite', 'area_of_interest']
    search_fields = ['area_of_interest__name']
    ordering_fields = ['acquisition_date', 'created_at']
    ordering = ['-acquisition_date']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return SatelliteImage.objects.none()
        user_areas = AreaOfInterest.objects.filter(created_by=user)
        return SatelliteImage.objects.filter(area_of_interest__in=user_areas)


class MonitoringDataViewSet(viewsets.ModelViewSet):
    """ViewSet for managing monitoring data"""
    serializer_class = MonitoringDataSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['area_of_interest', 'vegetation_index', 'satellite']
    search_fields = ['area_of_interest__name', 'vegetation_index__name']
    ordering_fields = ['acquisition_date', 'mean_value', 'created_at']
    ordering = ['-acquisition_date']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return MonitoringData.objects.none()
        user_areas = AreaOfInterest.objects.filter(created_by=user)
        return MonitoringData.objects.filter(area_of_interest__in=user_areas)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate monitoring data for an area"""
        try:
            data = request.data
            area_id = data.get('area_of_interest_id')
            vegetation_index_name = data.get('vegetation_index_name')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            satellite = data.get('satellite', 'SENTINEL2')
            
            if not all([area_id, vegetation_index_name, start_date, end_date]):
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get area
            try:
                area = AreaOfInterest.objects.get(id=area_id, created_by=request.user)
            except AreaOfInterest.DoesNotExist:
                return Response(
                    {'error': 'Area not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get vegetation index
            try:
                vegetation_index = VegetationIndex.objects.get(name=vegetation_index_name, is_active=True)
            except VegetationIndex.DoesNotExist:
                return Response(
                    {'error': 'Vegetation index not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calculate monitoring data
            calculator = VegetationIndexCalculator()
            result = calculator.calculate_for_area(
                area=area,
                vegetation_index=vegetation_index,
                start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
                satellite=satellite
            )
            
            if result:
                # Get created monitoring data
                monitoring_data = MonitoringData.objects.filter(
                    area_of_interest=area,
                    vegetation_index=vegetation_index,
                    acquisition_date__gte=start_date,
                    acquisition_date__lte=end_date
                ).order_by('acquisition_date')
                
                serializer = MonitoringDataSerializer(monitoring_data, many=True)
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'count': len(serializer.data)
                })
            else:
                return Response(
                    {'error': 'Failed to calculate monitoring data'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error calculating monitoring data: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MonitoringAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for managing monitoring alerts"""
    serializer_class = MonitoringAlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['severity', 'is_resolved', 'area_of_interest']
    search_fields = ['message', 'area_of_interest__name']
    ordering_fields = ['created_at', 'severity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return MonitoringAlert.objects.none()
        user_areas = AreaOfInterest.objects.filter(created_by=user)
        return MonitoringAlert.objects.filter(area_of_interest__in=user_areas)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert"""
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = datetime.now()
        alert.resolved_by = request.user
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)


class MonitoringConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing monitoring configurations"""
    serializer_class = MonitoringConfigurationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'area_of_interest']
    search_fields = ['area_of_interest__name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return MonitoringConfiguration.objects.none()
        user_areas = AreaOfInterest.objects.filter(created_by=user)
        return MonitoringConfiguration.objects.filter(area_of_interest__in=user_areas)


class HomeView(LoginRequiredMixin, TemplateView):
    """Home page view - requires authentication to access map dashboard"""
    template_name = 'index.html'
    login_url = '/accounts/login/'


def index_view(request):
    """Main dashboard view - requires authentication"""
    if not request.user.is_authenticated:
        return redirect('landing')
    return render(request, 'index.html')


class LandingView(TemplateView):
    """Landing page with different content for authenticated vs non-authenticated users"""
    template_name = 'monitoring/landing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_authenticated:
            # Get user's areas of interest
            areas = AreaOfInterest.objects.filter(created_by=user, is_active=True)
            context['areas'] = areas
            context['area_count'] = areas.count()
            
            # Get monitoring data count
            monitoring_data_count = MonitoringData.objects.filter(
                area_of_interest__in=areas
            ).count()
            context['monitoring_data_count'] = monitoring_data_count
            
            # Get recent alerts
            recent_alerts = MonitoringAlert.objects.filter(
                area_of_interest__in=areas,
                is_resolved=False
            ).order_by('-created_at')[:5]
            context['recent_alerts'] = recent_alerts
            context['alert_count'] = MonitoringAlert.objects.filter(
                area_of_interest__in=areas,
                is_resolved=False
            ).count()
        else:
            # For non-authenticated users, show sample data
            context['area_count'] = 0
            context['monitoring_data_count'] = 0
            context['alert_count'] = 0
            context['areas'] = []
            context['recent_alerts'] = []
        
        # Get educational tips (public)
        tips = Tip.objects.filter(is_active=True).order_by('order', '-created_at')[:10]
        context['tips'] = tips
        
        return context


class DemoView(TemplateView):
    """Demo page showing limited content preview"""
    template_name = 'monitoring/demo.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get a few sample tips
        tips = Tip.objects.filter(is_active=True).order_by('order', '-created_at')[:3]
        context['tips'] = tips
        return context
