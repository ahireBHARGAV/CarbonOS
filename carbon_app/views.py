from django.shortcuts import render, redirect
from django.db.models import Sum, F
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .models import CompanyConfig, Employee, DailyLog
import json
from datetime import datetime

# Helper for Superuser check
def is_admin(user):
    return user.is_superuser

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_superuser:
                return redirect('dashboard')
            else:
                return redirect('employee_dashboard_select') # Or direct to a default
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def employee_wizard_view(request):
    employees = Employee.objects.all()
    
    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        hours_worked = float(request.POST.get('hours_worked', 8.0))
        
        # Commute
        is_home_commute = request.POST.get('is_home_commute') == 'on'
        start_location = request.POST.get('start_location', '')
        commute_mode = request.POST.get('commute_mode', 'METRO')
        
        # Digital
        vcpu = float(request.POST.get('vcpu_hours', 0))
        storage = float(request.POST.get('storage_gb', 0))

        employee = Employee.objects.get(id=employee_id)
        
        # Create Log
        log = DailyLog(
            employee=employee,
            hours_worked=hours_worked,
            is_home_commute=is_home_commute,
            start_location=start_location,
            commute_mode=commute_mode,
            vcpu_hours=vcpu,
            storage_gb=storage
        )
        log.save()
        
        # Redirect to Employee Dashboard for this employee
        return redirect('employee_dashboard', employee_id=employee_id)

    return render(request, 'employee_wizard.html', {'employees': employees})

def employee_dashboard_select_view(request):
    # Simple view to select which employee dashboard to view (for prototype)
    employees = Employee.objects.all()
    return render(request, 'employee_dashboard_select.html', {'employees': employees})

def employee_dashboard_view(request, employee_id):
    employee = Employee.objects.get(id=employee_id)
    logs = DailyLog.objects.filter(employee=employee).order_by('-date')
    
    # Calculate Monthly Stats (Simple Sum for now)
    total_emissions = 0.0
    commute_emissions = 0.0
    digital_emissions = 0.0
    
    usage_data = [] # For Chart
    
    for log in logs:
        c = log.commute_emissions
        d = log.digital_carbon_footprint
        total = c + d
        
        commute_emissions += c
        digital_emissions += d
        total_emissions += total
        
        usage_data.append({
            'date': log.date.strftime("%Y-%m-%d"),
            'emission': round(total, 2)
        })
        
    context = {
        'employee': employee,
        'total_emissions': round(total_emissions, 2),
        'commute_emissions': round(commute_emissions, 2),
        'digital_emissions': round(digital_emissions, 2),
        'logs': logs[:5],
        'usage_chart_data': json.dumps(usage_data),
        'usage_chart_labels': json.dumps([x['date'] for x in usage_data][::-1]), # Reverse for chart
        'usage_chart_values': json.dumps([x['emission'] for x in usage_data][::-1]),
    }
    return render(request, 'employee_dashboard.html', context)

@user_passes_test(is_admin, login_url='/login/')
def dashboard_view(request):
    # Global Config
    config, _ = CompanyConfig.objects.get_or_create(id=1)
    
    if request.method == "POST":
        config.total_monthly_electricity_bill_kwh = float(request.POST.get('total_monthly_electricity_bill_kwh', config.total_monthly_electricity_bill_kwh))
        config.grid_intensity = float(request.POST.get('grid_intensity', config.grid_intensity))
        config.total_cloud_usage_kwh = float(request.POST.get('total_cloud_usage_kwh', config.total_cloud_usage_kwh))
        config.server_count = int(request.POST.get('server_count', config.server_count))
        config.save()
        return redirect('dashboard')
    
    # Aggregates
    logs = DailyLog.objects.select_related('employee').all().order_by('-date')
    total_hours = logs.aggregate(Sum('hours_worked'))['hours_worked__sum'] or 0.1 # Avoid div/0
    
    office_emissions_total = config.total_monthly_electricity_bill_kwh * config.grid_intensity
    cloud_emissions_total = config.total_cloud_usage_kwh * config.grid_intensity 
    
    commute_emissions_total = 0.0
    digital_emissions_total = 0.0
    
    for log in logs:
        commute_emissions_total += log.commute_emissions
        digital_emissions_total += log.digital_carbon_footprint
        
    total_emissions = office_emissions_total + cloud_emissions_total + commute_emissions_total + digital_emissions_total
    
    carbon_cost_per_hour = total_emissions / total_hours if total_hours > 0 else 0
    
    context = {
        'config': config,
        'logs': logs[:10], # Last 10
        'total_emissions': round(total_emissions, 2),
        'office_emissions': round(office_emissions_total, 2),
        'commute_emissions': round(commute_emissions_total, 2),
        'digital_emissions': round(digital_emissions_total + cloud_emissions_total, 2),
        'carbon_cost_per_hour': round(carbon_cost_per_hour, 4),
        'total_hours': round(total_hours, 1)
    }
    return render(request, 'dashboard.html', context)
