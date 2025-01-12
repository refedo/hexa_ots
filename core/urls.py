"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('raw-data/', views.raw_data, name='raw_data'),
    path('raw-data/edit/<int:id>/', views.raw_data_edit, name='raw_data_edit'),
    path('projects/', views.projects_view, name='projects'),
    path('projects/<str:project_number>/', views.project_detail, name='project_detail'),
    path('projects/<str:project_number>/edit/', views.project_edit, name='project_edit'),
    path('production/', views.production, name='production'),
    path('qc/', views.qc, name='qc'),
    path('logistics/', views.logistics, name='logistics'),
    path('material/', views.material, name='material'),
    
    # Production Management
    path('production/', views.production_management, name='production'),
    path('production/log/', views.production_logging, name='production_logging'),
    path('production/list/', views.production_list, name='production_list'),
    path('api/production/submit-log/', views.submit_production_log, name='submit_production_log'),
    path('api/production/get-log-designations/', views.get_log_designations, name='get_log_designations'),
    path('api/production/get-total-quantity/', views.get_total_quantity, name='get_total_quantity'),
    path('api/production/get-log-designation-details/', views.get_log_designation_details, name='get_log_designation_details'),
    
    # Production logging
    # path('production-logging/', views.production_logging, name='production_logging'),
    
    # API endpoints for CRUD operations
    path('api/projects/', include('projects.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
