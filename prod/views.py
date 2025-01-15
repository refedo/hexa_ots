from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum
from projects.models import RawData
from .models import ProductionLog
import json
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt

def production_logging(request):
    """View function for the production logging page."""
    return render(request, 'prod/production_logging.html')

def production_management(request):
    """Main production management view that serves as a dashboard/landing page for production-related activities."""
    return render(request, 'prod/production_management.html')

def production_list(request):
    """View function for displaying the list of production entries."""
    production_logs = ProductionLog.objects.all().order_by('-production_date')
    return render(request, 'prod/production_list.html', {'production_logs': production_logs})

def get_log_designations(request):
    """API endpoint to get log_designation items from RawData table."""
    search = request.GET.get('q', '')
    process = request.GET.get('process', '')
    
    # Query RawData for log designations
    query = RawData.objects.all()
    
    # Apply search filter if provided
    if search:
        query = query.filter(log_designation__icontains=search)
    
    # Get distinct log designations with their quantities
    log_designations = query.values('log_designation').annotate(
        available_quantity=Sum('quantity')
    ).order_by('log_designation')
    
    # Format results for Select2
    results = [
        {
            'id': item['log_designation'],
            'text': f"{item['log_designation']} (Qty: {item['available_quantity']})",
            'available_quantity': item['available_quantity']
        }
        for item in log_designations
    ]
    
    return JsonResponse({
        'results': results,
        'pagination': {'more': False}
    })

def get_total_quantity(request):
    """API endpoint to get total available quantity for selected log designations."""
    if request.method == 'POST':
        data = json.loads(request.body)
        log_designations = data.get('log_designations', [])
        
        total_quantity = RawData.objects.filter(
            log_designation__in=log_designations
        ).aggregate(
            total=Sum('net_weight_total')
        )['total'] or 0
        
        return JsonResponse({'total_quantity': float(total_quantity)})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_log_designation_details(request):
    """API endpoint to get details for a specific log designation."""
    log_designation = request.GET.get('log_designation')
    if log_designation:
        details = RawData.objects.filter(log_designation=log_designation).values(
            'log_designation',
            'profile',
            'grade',
            'part_mark',
            'assembly_mark',
            'sub_assembly_mark'
        ).first()
        
        if details:
            # Format the details nicely
            formatted_details = {
                'part_designation': details['part_mark'] or '',
                'name': f"{details['profile']} {details['grade']}",
                'assembly': details['assembly_mark'] or '',
                'sub_assembly': details['sub_assembly_mark'] or ''
            }
            return JsonResponse(formatted_details)
    
    return JsonResponse({'error': 'Log designation not found'}, status=404)

@csrf_exempt
def submit_production_log(request):
    """API endpoint to submit a new production log entry."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            process = data.get('process')
            items = data.get('items', [])
            
            if not process:
                return JsonResponse({'error': 'Process is required'}, status=400)
            if not items:
                return JsonResponse({'error': 'At least one item is required'}, status=400)
            
            # Get current date for all entries
            from datetime import date
            production_date = date.today()
            
            # Create production log entries for each item
            created_logs = []
            for item in items:
                log_designation = item.get('log_designation')
                quantity = item.get('quantity')
                
                if not log_designation or not quantity:
                    return JsonResponse({
                        'error': 'Log designation and quantity are required for all items'
                    }, status=400)
                
                production_log = ProductionLog.objects.create(
                    log_designation=log_designation,
                    production_date=production_date,
                    quantity=quantity,
                    process=process,
                    facility='default',  # You may want to make these configurable
                    team='default'       # You may want to make these configurable
                )
                created_logs.append(production_log.id)

            return JsonResponse({
                'message': 'Production logs created successfully',
                'ids': created_logs
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
