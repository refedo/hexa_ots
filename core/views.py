from django.shortcuts import render, redirect, get_object_or_404
from projects.models import Project, Building, RawData
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.db import models

def home(request):
    return render(request, 'home.html')

def dashboard(request):
    # Get project statistics
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(status='in_progress').count()
    completed_projects = Project.objects.filter(status='completed').count()

    # Get recent projects with related data
    recent_projects = Project.objects.select_related().all().order_by('-contract_date')[:5]
    recent_projects_data = []
    
    for project in recent_projects:
        status_colors = {
            'not_started': 'warning',
            'in_progress': 'primary',
            'completed': 'success'
        }
        recent_projects_data.append({
            'name': project.project_name or project.project_number,
            'status': project.get_status_display(),
            'status_color': status_colors.get(project.status, 'secondary'),
            'contract_date': project.contract_date.strftime('%Y-%m-%d') if project.contract_date else 'N/A',
            'client_name': project.client_name,
            'tonnage': project.contractual_tonnage
        })

    context = {
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'recent_projects': recent_projects_data,
    }
    return render(request, 'dashboard.html', context)

def raw_data(request):
    # Get raw data statistics
    raw_data_stats = RawData.objects.aggregate(
        total_quantity=Coalesce(Sum('quantity', default=0), 0),
        total_weight=Coalesce(Sum('net_weight_total', output_field=models.DecimalField()), Sum(0, output_field=models.DecimalField())),
    )
    
    # Get latest raw data entries with related data
    latest_entries = RawData.objects.select_related(
        'project', 'building'
    ).order_by('-id')[:10]
    
    # Format the statistics
    stats = {
        'total_quantity': raw_data_stats['total_quantity'] or 0,
        'total_weight': float(raw_data_stats['total_weight'] or 0)
    }
    
    context = {
        'stats': stats,
        'latest_entries': latest_entries
    }
    return render(request, 'raw_data.html', context)

def projects_view(request):
    # Get all projects with their buildings
    projects = Project.objects.prefetch_related('buildings').all().order_by('-contract_date')
    
    project_data = []
    for project in projects:
        buildings_count = project.buildings.count()
        project_data.append({
            'number': project.project_number,
            'name': project.project_name,
            'client': project.client_name,
            'manager': project.project_manager,
            'buildings': buildings_count,
            'tonnage': project.contractual_tonnage,
            'status': project.get_status_display(),
            'contract_date': project.contract_date
        })
    
    context = {
        'projects': project_data
    }
    return render(request, 'projects.html', context)

def production(request):
    # Get production-related raw data
    production_data = RawData.objects.select_related('project', 'building').all()
    
    context = {
        'production_data': production_data
    }
    return render(request, 'production.html', context)

def qc(request):
    # Get QC-related data from buildings
    buildings_with_qc = Building.objects.exclude(qc_inspection_date=None)
    
    context = {
        'buildings_with_qc': buildings_with_qc
    }
    return render(request, 'qc.html', context)

def logistics(request):
    # Get logistics-related raw data
    logistics_data = RawData.objects.select_related('project', 'building').all()
    
    context = {
        'logistics_data': logistics_data
    }
    return render(request, 'logistics.html', context)

def material(request):
    # Get material summaries from raw data
    material_summary = RawData.objects.values('profile', 'grade').annotate(
        total_quantity=Sum('quantity'),
        total_weight=Sum('net_weight_total')
    ).order_by('profile', 'grade')
    
    context = {
        'material_summary': material_summary
    }
    return render(request, 'material.html', context)

def project_detail(request, project_number):
    project = get_object_or_404(Project, project_number=project_number)
    buildings = project.buildings.all()
    raw_data = RawData.objects.filter(project=project)
    
    context = {
        'project': project,
        'buildings': buildings,
        'raw_data': raw_data
    }
    return render(request, 'project_detail.html', context)

def project_edit(request, project_number):
    project = get_object_or_404(Project, project_number=project_number)
    
    if request.method == 'POST':
        # Handle project update
        project.project_name = request.POST.get('project_name')
        project.client_name = request.POST.get('client_name')
        project.project_manager = request.POST.get('project_manager')
        project.contractual_tonnage = request.POST.get('contractual_tonnage')
        project.contract_date = request.POST.get('contract_date')
        project.save()
        
        return redirect('project_detail', project_number=project.project_number)
    
    context = {
        'project': project
    }
    return render(request, 'project_edit.html', context)

def raw_data_edit(request, id):
    entry = get_object_or_404(RawData, id=id)
    
    if request.method == 'POST':
        # Handle form submission
        pass
    
    context = {
        'entry': entry,
        'projects': Project.objects.all(),
        'buildings': Building.objects.filter(project=entry.project)
    }
    return render(request, 'raw_data_edit.html', context)
