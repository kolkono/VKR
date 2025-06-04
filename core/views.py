from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ServiceRequest, Cabinet, Device, ServiceLog, ReplacementRequest
from .forms import ServiceRequestForm, ServiceLogForm, DeviceReplacementReportForm
from .decorators import teacher_required, engineer_required, admin_required


@login_required
def home(request):
    # Разный контент для разных ролей
    if request.user.role == 'engineer':
        return redirect('engineer_dashboard')
    elif request.user.role == 'teacher':
        return redirect('my_requests')
    elif request.user.role == 'admin':
        return redirect('admin_dashboard')
    else:
        # Просто приветствие если роль не задана
        return render(request, 'core/home.html', {'user_name': request.user.username})


@login_required
@teacher_required
def my_requests(request):
    requests = ServiceRequest.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'core/my_requests.html', {'requests': requests, 'user_name': request.user.username})


@login_required
@teacher_required
def create_request(request):
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.created_by = request.user
            service_request.save()
            return redirect('my_requests')
    else:
        form = ServiceRequestForm()

    buildings = Cabinet.objects.values_list('building', flat=True).distinct()
    cabinets_qs = Cabinet.objects.prefetch_related('devices').all()
    cabinets = []
    for cabinet in cabinets_qs:
        cabinets.append({
            'id': cabinet.id,
            'building': cabinet.building,
            'number': cabinet.number,
            'devices': [{'id': device.id, 'name': device.name} for device in cabinet.devices.all()]
        })

    return render(request, 'core/create_request.html', {
        'form': form,
        'buildings': buildings,
        'cabinets': cabinets,
    })


@login_required
def devices_api(request):
    cabinet_id = request.GET.get('cabinet_id')
    if not cabinet_id:
        return JsonResponse([], safe=False)
    devices = Device.objects.filter(cabinet_id=cabinet_id).values('id', 'name', 'serial_number')
    return JsonResponse(list(devices), safe=False)


@login_required
@engineer_required
def engineer_dashboard(request):
    assigned_requests = ServiceRequest.objects.filter(
        assigned_engineer=request.user,
        is_completed=False
    ).select_related('device__cabinet').order_by('-created_at')

    return render(request, 'core/engineer_dashboard.html', {
        'requests': assigned_requests,
        'user_name': request.user.username,
    })


@login_required
@engineer_required
def engineer_request_detail(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_engineer=request.user)

    if request.method == 'POST':
        if 'submit_log' in request.POST:
            form = ServiceLogForm(request.POST)
            if form.is_valid():
                log = form.save(commit=False)
                log.request = service_request
                log.engineer = request.user
                log.save()

                if 'complete_request' in request.POST:
                    service_request.is_completed = True
                    service_request.save()
                return redirect('engineer_request_detail', request_id=request_id)
        elif 'replacement_request' in request.POST:
            if not service_request.requires_replacement:
                service_request.requires_replacement = True
                service_request.save()
            ReplacementRequest.objects.get_or_create(service_request=service_request, engineer=request.user)
            return redirect('engineer_request_detail', request_id=request_id)
    else:
        form = ServiceLogForm()

    logs = service_request.service_logs.select_related('engineer').order_by('-action_date')
    replacement_request = ReplacementRequest.objects.filter(service_request=service_request).first()

    return render(request, 'core/engineer_request_detail.html', {
        'request': service_request,
        'form': form,
        'logs': logs,
        'replacement_request': replacement_request,
    })


@login_required
@admin_required
def admin_dashboard(request):
    pending_replacements = ReplacementRequest.objects.filter(admin_approved=False).select_related(
        'service_request', 'engineer', 'service_request__device'
    ).order_by('-created_at')

    return render(request, 'core/admin_dashboard.html', {
        'pending_replacements': pending_replacements,
        'user_name': request.user.username,
    })


@login_required
@admin_required
def replacement_request_detail(request, replacement_id):
    replacement_request = get_object_or_404(ReplacementRequest, id=replacement_id, admin_approved=False)
    service_request = replacement_request.service_request

    if request.method == 'POST':
        form = DeviceReplacementReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.replacement_request = replacement_request
            report.created_by = request.user
            report.save()

            replacement_request.approve()
            service_request.is_completed = True
            service_request.save()

            return redirect('admin_dashboard')
    else:
        form = DeviceReplacementReportForm()

    return render(request, 'core/replacement_request_detail.html', {
        'replacement_request': replacement_request,
        'service_request': service_request,
        'form': form,
    })
