from django.contrib import admin
from .models import ProductionLog

@admin.register(ProductionLog)
class ProductionLogAdmin(admin.ModelAdmin):
    list_display = ('log_designation', 'quantity', 'process', 'production_date', 'facility', 'team', 'created_at')
    list_filter = ('process', 'facility', 'team')
    search_fields = ('log_designation', 'facility', 'team')
    ordering = ('-created_at',)
