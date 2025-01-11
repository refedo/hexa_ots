from django.shortcuts import render
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
