from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ServiceRequest, Cabinet, Device, ServiceLog, ReplacementRequest
from .forms import ServiceRequestForm, ServiceLogForm, DeviceReplacementReportForm
from .decorators import teacher_required, engineer_required, admin_required
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
def home(request):
    if request.user.role == 'engineer':
        return redirect('engineer_dashboard')
    elif request.user.role == 'teacher':
        return redirect('my_requests')
    elif request.user.role == 'admin':
        return redirect('admin_dashboard')
    else:
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

    unassigned_requests = ServiceRequest.objects.filter(
        assigned_engineer__isnull=True,
        is_completed=False
    ).select_related('device__cabinet').order_by('-created_at')

    requests = list(assigned_requests) + list(unassigned_requests)

    return render(request, 'core/engineer_dashboard.html', {
        'requests': requests,
        'user_name': request.user.username,
    })

@login_required
@engineer_required
def assign_request_to_self(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_engineer__isnull=True)
    service_request.assigned_engineer = request.user
    service_request.save()
    messages.success(request, f'Вы взяли заявку #{service_request.id} в работу.')
    return redirect('engineer_dashboard')

@login_required
@engineer_required
def engineer_request_detail(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_engineer=request.user)
    replacement_request = ReplacementRequest.objects.filter(service_request=service_request).first()

    if request.method == 'POST':
        form_log = ServiceLogForm(request.POST)
        if form_log.is_valid():
            log = form_log.save(commit=False)
            log.request = service_request
            log.engineer = request.user
            log.save()

            # Обработка завершения заявки
            if form_log.cleaned_data.get('complete_request'):
                service_request.is_completed = True
                service_request.is_paused = False  # Снимаем паузу, если заявка завершена
                service_request.save()

            # Обработка запроса на замену оборудования
            if form_log.cleaned_data.get('replacement_request'):
                # Создаём или обновляем ReplacementRequest
                if not replacement_request:
                    replacement_request = ReplacementRequest.objects.create(
                        service_request=service_request,
                        engineer=request.user,
                        reason=log.notes,
                        admin_approved=False,
                    )
                else:
                    replacement_request.reason = log.notes
                    replacement_request.admin_approved = False
                    replacement_request.save()

                # Ставим паузу и флаг requires_replacement
                service_request.requires_replacement = True
                service_request.is_paused = True
                service_request.save()

            return redirect('engineer_request_detail', request_id=request_id)

        # Обработка отчёта по замене, если админ одобрил (на случай, если есть форма отчёта)
        elif 'replacement_report' in request.POST and replacement_request and replacement_request.admin_approved:
            form_report = DeviceReplacementReportForm(request.POST)
            if form_report.is_valid():
                report = form_report.save(commit=False)
                report.replacement_request = replacement_request
                report.save()

                # Завершаем заявку и снимаем паузу
                service_request.is_completed = True
                service_request.is_paused = False
                service_request.save()

                messages.success(request, 'Отчёт по замене успешно сохранён и заявка закрыта.')
                return redirect('engineer_request_detail', request_id=request_id)
    else:
        form_log = ServiceLogForm()
        form_report = DeviceReplacementReportForm()
        if replacement_request and replacement_request.admin_approved:
            form_report = DeviceReplacementReportForm(instance=replacement_request.device_replacement_report_set.last())

    logs = service_request.service_logs.select_related('engineer').order_by('-action_date')

    context = {
        'request': service_request,
        'form_log': form_log,
        'form_report': form_report,
        'logs': logs,
        'replacement_request': replacement_request,
    }
    return render(request, 'core/engineer_request_detail.html', context)

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

            # Одобряем запрос замены
            replacement_request.admin_approved = True
            replacement_request.save()

            # Снимаем паузу и требование замены
            service_request.requires_replacement = False
            service_request.is_paused = False
            service_request.save()

            messages.success(request, f'Запрос замены №{replacement_request.id} успешно подтвержден.')
            return redirect('admin_dashboard')
    else:
        form = DeviceReplacementReportForm()

    return render(request, 'core/replacement_request.html', {
        'replacement_request': replacement_request,
        'service_request': service_request,
        'form': form,
    })

@login_required
def active_requests(request):
    if request.user.role != 'engineer':
        return redirect('login')
    requests = ServiceRequest.objects.filter(assigned_engineer=request.user, is_completed=False)
    return render(request, 'engineer/active_requests.html', {'requests': requests})

@login_required
@engineer_required
def completed_requests(request):
    qs = ServiceRequest.objects.filter(
        assigned_engineer=request.user,
        is_completed=True
    ).select_related('device__cabinet')

    building = request.GET.get('building')
    cabinet_id = request.GET.get('cabinet')

    if building:
        qs = qs.filter(device__cabinet__building=building)

    if cabinet_id:
        qs = qs.filter(device__cabinet__id=cabinet_id)

    buildings = Cabinet.objects.values_list('building', flat=True).distinct()
    cabinets = Cabinet.objects.all()

    return render(request, 'engineer/completed_requests.html', {
        'requests': qs.order_by('-created_at'),
        'buildings': buildings,
        'cabinets': cabinets,
        'selected_building': building,
        'selected_cabinet': cabinet_id,
    })

@login_required
def profile_view(request):
    user = request.user
    return render(request, 'core/profile.html', {'user': user})

# Админские представления

@login_required
@user_passes_test(is_admin)
def admin_replacement_requests(request):
    requests = ReplacementRequest.objects.all().order_by('-created_at')
    return render(request, 'core/admin_replacement_requests.html', {'requests': requests})

@login_required
@user_passes_test(is_admin)
def admin_approve_replacement(request, request_id):
    replacement_request = get_object_or_404(ReplacementRequest, id=request_id, admin_approved=False)
    replacement_request.admin_approved = True
    replacement_request.save()
    messages.success(request, f'Запрос замены №{replacement_request.id} успешно одобрен.')
    return redirect('admin_replacement_requests')

@login_required
@user_passes_test(is_admin)
def admin_reject_replacement(request, request_id):
    replacement_request = get_object_or_404(ReplacementRequest, id=request_id, admin_approved=False)
    replacement_request.delete()
    messages.info(request, f'Запрос замены №{replacement_request.id} отклонён и удалён.')
    return redirect('admin_replacement_requests')
