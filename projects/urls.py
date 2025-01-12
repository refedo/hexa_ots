from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, BuildingViewSet, RawDataViewSet, add_building,
    production_logging, get_assembly_parts, get_total_quantity, log_production
)

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'buildings', BuildingViewSet)
router.register(r'rawdata', RawDataViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('projects/<str:project_number>/add-building/', add_building, name='add_building'),
    path('production-logging/', production_logging, name='production_logging'),
    path('api/assembly-parts/', get_assembly_parts, name='get_assembly_parts'),
    path('api/total-quantity/', get_total_quantity, name='get_total_quantity'),
    path('api/log-production/', log_production, name='log_production'),
]
