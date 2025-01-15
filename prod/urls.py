from django.urls import path
from . import views

app_name = 'prod'

urlpatterns = [
    path('', views.production_management, name='management'),
    path('logging/', views.production_logging, name='logging'),
    path('list/', views.production_list, name='list'),
    path('api/log-designations/', views.get_log_designations, name='get_log_designations'),
    path('api/total-quantity/', views.get_total_quantity, name='get_total_quantity'),
    path('api/log-designation-details/', views.get_log_designation_details, name='get_log_designation_details'),
    path('api/submit/', views.submit_production_log, name='submit_production_log'),
]
