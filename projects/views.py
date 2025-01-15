from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
import pandas as pd
from .models import Project, Building, RawData
from .serializers import (
    ProjectSerializer, BuildingSerializer, RawDataSerializer,
    RawDataUploadSerializer, LogDesignationSerializer
)
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError

# Create your views here.

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'project_nature', 'structure_type', 'client_name', 'project_manager']
    search_fields = ['project_number', 'project_name', 'estimation_number', 'client_name']
    ordering_fields = ['created_at', 'updated_at', 'project_number', 'client_name']
    ordering = ['-created_at']

    @action(detail=True, methods=['get'])
    def buildings(self, request, pk=None):
        project = self.get_object()
        buildings = Building.objects.filter(project=project)
        serializer = BuildingSerializer(buildings, many=True)
        return Response(serializer.data)

class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'erection_applicable']
    search_fields = ['building_name', 'designer_name', 'subcontractor_name']
    ordering_fields = ['building_name', 'created_at', 'planned_start_date', 'actual_start_date']
    ordering = ['building_name']

class RawDataFilter(django_filters.FilterSet):
    log_designation = django_filters.CharFilter(lookup_expr='icontains')
    project_number = django_filters.CharFilter(field_name='project__project_number', lookup_expr='icontains')
    building_name = django_filters.CharFilter(field_name='building__building_name', lookup_expr='icontains')

    class Meta:
        model = RawData
        fields = ['project', 'building', 'log_designation', 'profile', 'grade']

class RawDataViewSet(viewsets.ModelViewSet):
    queryset = RawData.objects.all()
    serializer_class = RawDataSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RawDataFilter
    search_fields = ['log_designation', 'part_mark', 'assembly_mark', 'sub_assembly_mark']
    ordering_fields = ['log_designation', 'part_mark', 'profile']

    @action(detail=False, methods=['get'])
    def by_log_designation(self, request):
        """
        Get raw data filtered by log designation with project and building details.
        Query parameters:
        - log_designation: Filter by log designation (partial match)
        - project: Filter by project ID
        - building: Filter by building ID
        """
        queryset = self.get_queryset()
        log_designation = request.query_params.get('log_designation', None)
        project_id = request.query_params.get('project', None)
        building_id = request.query_params.get('building', None)

        if log_designation:
            queryset = queryset.filter(log_designation__icontains=log_designation)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if building_id:
            queryset = queryset.filter(building_id=building_id)

        serializer = LogDesignationSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def upload_excel(self, request):
        serializer = RawDataUploadSerializer(data=request.data)
        if serializer.is_valid():
            project = serializer.validated_data['project']
            building = serializer.validated_data['building']
            excel_file = serializer.validated_data['file']

            try:
                df = pd.read_excel(excel_file)
                raw_data_objects = []

                for _, row in df.iterrows():
                    if not row.get('log_designation'):
                        continue  # Skip rows without log_designation

                    raw_data = RawData(
                        project=project,
                        building=building,
                        log_designation=row['log_designation'],
                        part_designation=row.get('part_designation'),
                        assembly_mark=row.get('assembly_mark'),
                        sub_assembly_mark=row.get('sub_assembly_mark'),
                        part_mark=row.get('part_mark'),
                        quantity=row.get('quantity'),
                        name=row.get('name'),
                        profile=row.get('profile'),
                        grade=row.get('grade'),
                        length=row.get('length'),
                        net_area_single=row.get('net_area_single'),
                        net_area_all=row.get('net_area_all'),
                        single_part_weight=row.get('single_part_weight'),
                        net_weight_total=row.get('net_weight_total'),
                        revision=row.get('revision')
                    )
                    raw_data_objects.append(raw_data)

                RawData.objects.bulk_create(raw_data_objects)
                return Response({
                    'message': f'Successfully uploaded {len(raw_data_objects)} records',
                    'skipped': len(df) - len(raw_data_objects)
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def add_building(request, project_number):
    project = get_object_or_404(Project, project_number=project_number)
    
    if request.method == 'POST':
        # Handle form submission for adding a new building
        building_name = request.POST.get('building_name')
        designer_name = request.POST.get('designer_name')
        subcontractor_name = request.POST.get('subcontractor_name')
        
        # Create a new Building instance
        new_building = Building(
            project=project,
            building_name=building_name,
            designer_name=designer_name,
            subcontractor_name=subcontractor_name
        )
        new_building.save()
        return redirect('project_detail', project_number=project_number)
    
    context = {
        'project': project
    }
    return render(request, 'add_building.html', context)

def project_detail(request, project_number):
    """View function for displaying project details."""
    project = get_object_or_404(Project, project_number=project_number)
    buildings = Building.objects.filter(project=project)
    raw_data = RawData.objects.filter(project=project)
    
    context = {
        'project': project,
        'buildings': buildings,
        'raw_data': raw_data
    }
    return render(request, 'projects/project_detail.html', context)

def projects_list(request):
    """View function for displaying the list of projects."""
    projects = Project.objects.all().order_by('-created_at')
    return render(request, 'projects/project_list.html', {'projects': projects})

def production_logging(request):
    """View for the production logging page"""
    return render(request, 'production_logging.html')

@require_http_methods(["GET"])
def get_assembly_parts(request):
    """API endpoint to get assembly parts for select2"""
    search = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    page_size = 10
    
    # Filter assembly parts from raw data
    parts = RawData.objects.filter(
        part_designation='Assembly Parts',
        log_designation__icontains=search
    ).values('log_designation').distinct()
    
    # Implement pagination
    start = (page - 1) * page_size
    end = start + page_size
    
    results = [{'id': part['log_designation'], 'text': part['log_designation']} 
              for part in parts[start:end]]
    
    return JsonResponse({
        'results': results,
        'pagination': {'more': len(parts) > end}
    })

@require_http_methods(["GET"])
def get_total_quantity(request):
    """Get total quantity for selected parts"""
    parts = request.GET.get('parts', '').split(',')
    total = RawData.objects.filter(
        log_designation__in=parts
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    return JsonResponse({'total_quantity': total})

@require_http_methods(["POST"])
def log_production(request):
    """Handle production log submission"""
    try:
        # Get form data
        log_designations = request.POST.getlist('log_designation')
        quantity = int(request.POST.get('quantity'))
        process = request.POST.get('process')
        production_date = request.POST.get('production_date')
        facility = request.POST.get('facility')
        team = request.POST.get('team')
        
        # TODO: Create ProductionLog model and save the data
        # For now, we'll just return success
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def get_buildings(request):
    """Get buildings for a project."""
    project_id = request.GET.get('project')
    print(f"DEBUG: get_buildings called with project_id: {project_id}")
    
    if not project_id:
        print("DEBUG: No project_id provided")
        return JsonResponse({'error': 'No project ID provided'}, status=400)
    
    try:
        # Get buildings for project
        buildings = Building.objects.filter(project_id=project_id)
        print(f"DEBUG: Found {buildings.count()} buildings for project {project_id}")
        
        # Convert to list of dictionaries
        building_list = [{'id': b.id, 'building_name': b.building_name} for b in buildings]
        print(f"DEBUG: Building list: {building_list}")
        
        return JsonResponse(building_list, safe=False)
    except Exception as e:
        print(f"DEBUG: Error in get_buildings: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
