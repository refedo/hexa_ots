from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.urls import reverse
import pandas as pd
import io
from .models import Project, Building, RawData, ProductionLog

# Register your models here.

class BuildingInline(admin.TabularInline):
    model = Building
    extra = 1
    fieldsets = None
    fields = (
        'building_name', 'designer_name', 'subcontractor_name',
        ('design_start_date', 'design_end_date'),
        ('shop_drawing_start_date', 'shop_drawing_end_date'),
        ('production_start_date', 'production_end_date'),
        'erection_applicable',
        ('erection_start_date', 'erection_end_date'),
    )
    classes = ['collapse']
    verbose_name = "Building"
    verbose_name_plural = "Buildings"

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_number', 'project_name', 'client_name', 'status', 'created_at')
    list_filter = ('status', 'project_nature', 'structure_type', 'client_name')
    search_fields = ('project_number', 'project_name', 'estimation_number', 'client_name')
    ordering = ('-created_at',)
    inlines = [BuildingInline]

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('building_name', 'project', 'designer_name', 'subcontractor_name', 'planned_start_date', 'actual_end_date')
    list_filter = ('project', 'erection_applicable')
    search_fields = ('building_name', 'designer_name', 'subcontractor_name')
    ordering = ('building_name',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('project', 'building_name', 'designer_name', 'subcontractor_name')
        }),
        ('Design Phase', {
            'fields': ('design_start_date', 'design_end_date')
        }),
        ('Shop Drawing Phase', {
            'fields': ('shop_drawing_start_date', 'shop_drawing_end_date')
        }),
        ('Production Phase', {
            'fields': ('production_start_date', 'production_end_date')
        }),
        ('Erection Phase', {
            'fields': ('erection_applicable', 'erection_start_date', 'erection_end_date')
        }),
        ('Planning', {
            'fields': ('planned_start_date', 'planned_end_date')
        }),
        ('Actual Timeline', {
            'fields': ('actual_start_date', 'actual_end_date')
        }),
        ('Quality Control', {
            'fields': ('qc_inspection_date',)
        })
    )

@admin.register(RawData)
class RawDataAdmin(admin.ModelAdmin):
    list_display = ('log_designation', 'project', 'building', 'profile', 'quantity', 'grade')
    list_filter = ('project', 'building', 'profile', 'grade')
    search_fields = ('log_designation', 'part_mark', 'assembly_mark', 'sub_assembly_mark')
    ordering = ('log_designation',)
    change_list_template = 'admin/projects/rawdata/change_list.html'
    change_form_template = 'admin/projects/rawdata/change_form.html'

    fieldsets = (
        ('Project Information', {
            'fields': ('project', 'building')
        }),
        ('Part Information', {
            'fields': (
                'log_designation',
                ('part_designation', 'assembly_mark'),
                ('sub_assembly_mark', 'part_mark'),
                ('quantity', 'name')
            ),
            'description': 'Log designation is the primary identifier for production, QC, logistics, and erection activities.'
        }),
        ('Technical Details', {
            'fields': (
                'profile', 'grade', 'length',
                'net_area_single', 'net_area_all',
                'single_part_weight', 'net_weight_total',
                'revision'
            ),
            'classes': ('collapse',)
        })
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-excel/', self.upload_excel, name='rawdata_upload_excel'),
            path('download-sample/', self.download_sample_excel, name='download_sample_excel'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['projects'] = Project.objects.all()
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        
        # Get current object's project and building
        current_obj = self.get_object(request, object_id)
        if current_obj:
            # Get next and previous objects within the same project and building
            next_obj = RawData.objects.filter(
                project=current_obj.project,
                building=current_obj.building,
                id__gt=object_id
            ).order_by('id').first()

            previous_obj = RawData.objects.filter(
                project=current_obj.project,
                building=current_obj.building,
                id__lt=object_id
            ).order_by('-id').first()

            extra_context['next_id'] = next_obj.id if next_obj else None
            extra_context['previous_id'] = previous_obj.id if previous_obj else None

        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def download_sample_excel(self, request):
        # Create sample data
        sample_data = {
            'log_designation': ['LOG-001', 'LOG-002'],
            'part_designation': ['PART-001', 'PART-002'],
            'assembly_mark': ['ASM-001', 'ASM-002'],
            'sub_assembly_mark': ['SUB-001', 'SUB-002'],
            'part_mark': ['PM-001', 'PM-002'],
            'quantity': [1, 2],
            'name': ['Sample Part 1', 'Sample Part 2'],
            'profile': ['IPE 200', 'HEA 300'],
            'grade': ['S275JR', 'S355JR'],
            'length': [6000.00, 8000.00],
            'net_area_single': ['10.5', '15.7'],
            'net_area_all': [10.50, 31.40],
            'single_part_weight': [125.50, 267.80],
            'net_weight_total': ['125.50', '535.60'],
            'revision': ['A', 'B']
        }
        
        df = pd.DataFrame(sample_data)
        
        # Create Excel file in memory
        excel_file = io.BytesIO()
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sample Data')
        
        # Prepare response
        excel_file.seek(0)
        response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=raw_data_sample.xlsx'
        
        return response

    def upload_excel(self, request):
        if request.method == 'POST':
            try:
                excel_file = request.FILES['excel_file']
                project_id = request.POST.get('project')
                building_id = request.POST.get('building')

                if not project_id or not building_id:
                    raise ValueError("Project and Building must be selected")

                project = Project.objects.get(id=project_id)
                building = Building.objects.get(id=building_id)

                df = pd.read_excel(excel_file)
                raw_data_objects = []

                # Helper function to handle NaN values for decimal fields
                def clean_decimal(value):
                    if pd.isna(value) or value == '':
                        return None
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return None

                for _, row in df.iterrows():
                    if not row.get('log_designation') or pd.isna(row.get('log_designation')):
                        continue  # Skip rows without log_designation

                    raw_data = RawData(
                        project=project,
                        building=building,
                        log_designation=str(row['log_designation']).strip(),
                        part_designation=str(row.get('part_designation', '')) if not pd.isna(row.get('part_designation')) else None,
                        assembly_mark=str(row.get('assembly_mark', '')) if not pd.isna(row.get('assembly_mark')) else None,
                        sub_assembly_mark=str(row.get('sub_assembly_mark', '')) if not pd.isna(row.get('sub_assembly_mark')) else None,
                        part_mark=str(row.get('part_mark', '')) if not pd.isna(row.get('part_mark')) else None,
                        quantity=int(row['quantity']) if not pd.isna(row.get('quantity')) else None,
                        name=str(row.get('name', '')) if not pd.isna(row.get('name')) else None,
                        profile=str(row.get('profile', '')) if not pd.isna(row.get('profile')) else None,
                        grade=str(row.get('grade', '')) if not pd.isna(row.get('grade')) else None,
                        length=clean_decimal(row.get('length')),
                        net_area_single=str(row.get('net_area_single', '')) if not pd.isna(row.get('net_area_single')) else None,
                        net_area_all=clean_decimal(row.get('net_area_all')),
                        single_part_weight=clean_decimal(row.get('single_part_weight')),
                        net_weight_total=str(row.get('net_weight_total', '')) if not pd.isna(row.get('net_weight_total')) else None,
                        revision=str(row.get('revision', '')) if not pd.isna(row.get('revision')) else None
                    )
                    raw_data_objects.append(raw_data)

                RawData.objects.bulk_create(raw_data_objects)
                self.message_user(
                    request,
                    f'Successfully uploaded {len(raw_data_objects)} records. Skipped {len(df) - len(raw_data_objects)} records without log designation.',
                    messages.SUCCESS
                )
            except ValueError as ve:
                self.message_user(request, str(ve), messages.ERROR)
            except Exception as e:
                self.message_user(request, f'Error uploading file: {str(e)}', messages.ERROR)

        return HttpResponseRedirect('../')

@admin.register(ProductionLog)
class ProductionLogAdmin(admin.ModelAdmin):
    list_display = ('log_designation', 'quantity', 'process', 'production_date', 'facility', 'team', 'created_at')
    list_filter = ('process', 'facility', 'team')
    search_fields = ('log_designation', 'facility', 'team')
    ordering = ('-created_at',)
