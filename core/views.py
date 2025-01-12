from django.shortcuts import render, redirect, get_object_or_404
from projects.models import Project, Building, RawData, ProductionLog
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.db import models
from django.http import JsonResponse
from projects.models import RawData  
import json

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

def production_logging(request):
    """
    View function for the production logging page.
    """
    context = {}
    return render(request, 'production_logging.html', context)

def production_management(request):
    """
    Main production management view that serves as a dashboard/landing page for production-related activities.
    """
    return render(request, 'production_management.html', {
        'section': 'production'
    })

def production_logging_view(request):
    """
    View function for logging new production entries.
    """
    return render(request, 'production_logging.html', {
        'section': 'production'
    })

def production_list(request):
    """
    View function for displaying the list of production entries.
    """
    production_logs = ProductionLog.objects.all().order_by('-production_date', '-created_at')
    return render(request, 'production_list.html', {
        'section': 'production',
        'production_logs': production_logs
    })

def get_log_designations(request):
    """
    API endpoint to get log_designation items from RawData table.
    """
    search_term = request.GET.get('q', '')
    process = request.GET.get('process', '')
    
    if not process:
        return JsonResponse({'error': 'Process type is required'}, status=400)

    # Get all raw data items
    raw_data = RawData.objects.filter(
        log_designation__icontains=search_term
    ).distinct()

    # Get the quantities already used for each log_designation in the specified process
    used_quantities = ProductionLog.objects.filter(
        process=process
    ).values('log_designation').annotate(
        used_quantity=Sum('quantity')
    )

    # Convert to dictionary for easier lookup
    used_qty_dict = {item['log_designation']: item['used_quantity'] for item in used_quantities}

    # Filter and format results
    results = []
    for item in raw_data:
        total_qty = item.quantity or 0
        used_qty = used_qty_dict.get(item.log_designation, 0)
        available_qty = total_qty - used_qty

        if available_qty > 0:
            results.append({
                'id': item.log_designation,
                'text': f"{item.log_designation} - {item.name or 'N/A'} ({available_qty} available)",
                'available_quantity': available_qty
            })

    return JsonResponse({
        'results': results
    })

def get_total_quantity(request):
    """
    API endpoint to get total available quantity for selected log designations.
    """
    parts = request.GET.get('parts', '').split(',')
    if not parts or parts[0] == '':
        return JsonResponse({'total_quantity': 0})
    
    # Sum the quantities for the selected log designations
    total = RawData.objects.filter(
        log_designation__in=parts
    ).aggregate(
        total_quantity=Coalesce(Sum('quantity'), 0)
    )['total_quantity']
    
    return JsonResponse({'total_quantity': total})

def get_log_designation_details(request):
    """
    API endpoint to get details for a specific log designation.
    """
    log_designation = request.GET.get('log_designation', '')
    
    if not log_designation:
        return JsonResponse({'error': 'Log designation is required'}, status=400)
    
    # Get the total quantity and other details for this log designation
    item = RawData.objects.filter(log_designation=log_designation).first()
    
    if not item:
        return JsonResponse({'error': 'Log designation not found'}, status=404)
    
    details = {
        'quantity': item.quantity or 0,
        'part_designation': item.part_designation or '',
        'assembly_mark': item.assembly_mark or '',
        'name': item.name or ''
    }
    
    return JsonResponse(details)

def submit_production_log(request):
    """
    API endpoint to submit a new production log entry.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        # Get form data
        production_date = request.POST.get('production_date')
        process = request.POST.get('process')
        facility = request.POST.get('facility')
        team = request.POST.get('team')
        quantities = json.loads(request.POST.get('quantities', '{}'))
        
        # Validate required fields
        if not all([production_date, process, facility, team, quantities]):
            return JsonResponse({'error': 'All fields are required'}, status=400)
        
        # Create production log entries for each item
        logs = []
        for log_designation, quantity in quantities.items():
            log = ProductionLog.objects.create(
                log_designation=log_designation,
                quantity=quantity,
                process=process,
                production_date=production_date,
                facility=facility,
                team=team
            )
            logs.append(log)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully created {len(logs)} production log entries'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid quantities data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
