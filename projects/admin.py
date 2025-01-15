from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.urls import reverse
import pandas as pd
import io
from .models import Project, Building, RawData

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

class ProjectFilter(admin.SimpleListFilter):
    title = 'Project'
    parameter_name = 'project'

    def lookups(self, request, model_admin):
        projects = Project.objects.all()
        return [(str(project.id), f"{project.project_number} - {project.project_name}") for project in projects]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(project_id=self.value())
        return queryset

class BuildingFilter(admin.SimpleListFilter):
    title = 'Building'
    parameter_name = 'building'

    def lookups(self, request, model_admin):
        project_id = request.GET.get('project')
        if project_id:
            try:
                buildings = Building.objects.filter(project_id=project_id)
                return [(str(building.id), building.building_name) for building in buildings]
            except (Project.DoesNotExist, ValueError):
                return []
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(building_id=self.value())
        return queryset

@admin.register(RawData)
class RawDataAdmin(admin.ModelAdmin):
    list_display = ('log_designation', 'project', 'building', 'profile', 'quantity', 'grade')
    list_filter = (ProjectFilter, BuildingFilter, 'profile', 'grade')
    search_fields = ('log_designation', 'part_mark', 'assembly_mark', 'sub_assembly_mark')
    ordering = ('log_designation',)
    change_list_template = 'admin/projects/rawdata/change_list.html'
    change_form_template = 'admin/projects/rawdata/change_form.html'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "building":
            # Get project_id from either GET params or existing object
            project_id = request.GET.get('project')
            if not project_id and hasattr(request, 'resolver_match'):
                object_id = request.resolver_match.kwargs.get('object_id')
                if object_id:
                    try:
                        raw_data = RawData.objects.get(id=object_id)
                        project_id = raw_data.project_id
                        # Pre-select the building if we have a project
                        if project_id:
                            kwargs["queryset"] = Building.objects.filter(project_id=project_id)
                            kwargs["initial"] = raw_data.building_id
                    except RawData.DoesNotExist:
                        kwargs["queryset"] = Building.objects.none()
            else:
                if project_id:
                    kwargs["queryset"] = Building.objects.filter(project_id=project_id)
                else:
                    kwargs["queryset"] = Building.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:  # Editing existing object
            form.base_fields['building'].queryset = Building.objects.filter(project=obj.project)
        else:  # Creating new object
            project_id = request.GET.get('project')
            if project_id:
                try:
                    form.base_fields['project'].initial = Project.objects.get(id=project_id)
                    form.base_fields['building'].queryset = Building.objects.filter(project_id=project_id)
                except Project.DoesNotExist:
                    form.base_fields['building'].queryset = Building.objects.none()
            else:
                form.base_fields['building'].queryset = Building.objects.none()
        return form

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['projects'] = Project.objects.all()
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('upload-excel/', self.upload_excel, name='rawdata_upload_excel'),
            path('download-sample/', self.download_sample, name='rawdata_download_sample'),
        ]
        return my_urls + urls

    def upload_excel(self, request):
        if request.method == 'POST':
            project_id = request.POST.get('project')
            building_id = request.POST.get('building')
            excel_file = request.FILES.get('excel_file')

            if not all([project_id, building_id, excel_file]):
                messages.error(request, 'Please provide all required fields')
                return HttpResponseRedirect('../')

            try:
                project = Project.objects.get(id=project_id)
                building = Building.objects.get(id=building_id, project=project)
                
                df = pd.read_excel(excel_file)
                
                for _, row in df.iterrows():
                    RawData.objects.create(
                        project=project,
                        building=building,
                        log_designation=row.get('Log Designation', 'PENDING'),
                        part_designation=row.get('Part Designation'),
                        assembly_mark=row.get('Assembly Mark'),
                        sub_assembly_mark=row.get('Sub Assembly Mark'),
                        part_mark=row.get('Part Mark'),
                        quantity=row.get('Quantity'),
                        name=row.get('Name'),
                        profile=row.get('Profile'),
                        grade=row.get('Grade'),
                        length=row.get('Length'),
                        net_area_single=row.get('Net Area Single'),
                        net_area_all=row.get('Net Area All'),
                        single_part_weight=row.get('Single Part Weight'),
                        net_weight_total=row.get('Net Weight Total'),
                        revision=row.get('Revision')
                    )
                
                messages.success(request, 'Excel file uploaded successfully')
            except (Project.DoesNotExist, Building.DoesNotExist):
                messages.error(request, 'Invalid project or building selected')
            except Exception as e:
                messages.error(request, f'Error uploading file: {str(e)}')
            
            return HttpResponseRedirect('../')
        
        return HttpResponseRedirect('../')

    def download_sample(self, request):
        sample_data = {
            'Log Designation': ['LOG001', 'LOG002'],
            'Part Designation': ['PART001', 'PART002'],
            'Assembly Mark': ['ASM001', 'ASM002'],
            'Sub Assembly Mark': ['SUBASM001', 'SUBASM002'],
            'Part Mark': ['PM001', 'PM002'],
            'Quantity': [1, 2],
            'Name': ['Item 1', 'Item 2'],
            'Profile': ['Profile A', 'Profile B'],
            'Grade': ['Grade 1', 'Grade 2'],
            'Length': [100.5, 200.5],
            'Net Area Single': ['10.5', '20.5'],
            'Net Area All': [100.5, 200.5],
            'Single Part Weight': [50.5, 75.5],
            'Net Weight Total': [50.5, 151.0],
            'Revision': ['Rev A', 'Rev B']
        }
        
        df = pd.DataFrame(sample_data)
        
        # Create the Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        # Set up the response
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=raw_data_sample.xlsx'
        
        return response

    class Media:
        js = ['admin/js/jquery.init.js']
