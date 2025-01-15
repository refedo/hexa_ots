from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, BuildingViewSet, RawDataViewSet, add_building,
    production_logging, get_assembly_parts, get_total_quantity, log_production,
    projects_list, project_detail, get_buildings
)

app_name = 'projects'

router = DefaultRouter()
router.register(r'api/projects', ProjectViewSet)
router.register(r'api/buildings', BuildingViewSet)
router.register(r'api/rawdata', RawDataViewSet)

urlpatterns = [
    path('', projects_list, name='project-list'),
    path('get-buildings/', get_buildings, name='get_buildings'),
    path('<str:project_number>/', project_detail, name='project-detail'),
    path('<str:project_number>/add-building/', add_building, name='add_building'),
    path('api/', include(router.urls)),
    path('api/assembly-parts/', get_assembly_parts, name='get_assembly_parts'),
    path('api/total-quantity/', get_total_quantity, name='get_total_quantity'),
    path('api/log-production/', log_production, name='log_production'),
]
