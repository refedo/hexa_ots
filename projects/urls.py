from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, BuildingViewSet, RawDataViewSet, add_building,
    production_logging, get_assembly_parts, get_total_quantity, log_production,
    projects_list, project_detail, get_buildings
)

app_name = 'projects'

# Main URL patterns
urlpatterns = [
    # Main views
    path('', projects_list, name='project-list'),
    path('<str:project_number>/', project_detail, name='project-detail'),
    path('<str:project_number>/add-building/', add_building, name='add_building'),
    path('get-buildings/', get_buildings, name='get_buildings'),
]

# API endpoints
api_patterns = [
    path('assembly-parts/', get_assembly_parts, name='get_assembly_parts'),
    path('total-quantity/', get_total_quantity, name='get_total_quantity'),
    path('log-production/', log_production, name='log_production'),
]

# API router configuration
router = DefaultRouter()
router.register('api/projects', ProjectViewSet)  # Changed path prefix
router.register('api/buildings', BuildingViewSet)  # Changed path prefix
router.register('api/rawdata', RawDataViewSet)  # Changed path prefix

# Add API URLs
urlpatterns += api_patterns
urlpatterns += router.urls  # Include router URLs directly
