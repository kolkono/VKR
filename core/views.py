from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ServiceRequest, Cabinet, Device, ServiceLog, ReplacementRequest, DeviceReplacementReport
from .forms import ServiceRequestForm, ServiceLogForm, DeviceReplacementReportForm
from .decorators import teacher_required, engineer_required, admin_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q



def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
def home(request):
    if request.user.role == 'engineer':
        return redirect('engineer_dashboard')
    elif request.user.role == 'teacher':
        return redirect('teacher_dashboard')  # ✅ сюда!
    elif request.user.role == 'admin':
        return redirect('admin_dashboard')


@login_required
@teacher_required
def my_requests(request):
    qs = ServiceRequest.objects.filter(created_by=request.user).select_related('device__cabinet').order_by('-created_at')

    # Фильтры
    building = request.GET.get('building')
    cabinet_id = request.GET.get('cabinet')

    if building:
        qs = qs.filter(device__cabinet__building=building)
    if cabinet_id:
        qs = qs.filter(device__cabinet__id=cabinet_id)

    buildings = Cabinet.objects.values_list('building', flat=True).distinct()
    cabinets = Cabinet.objects.all()

    return render(request, 'core/my_requests.html', {
        'requests': qs,
        'buildings': buildings,
        'cabinets': cabinets,
        'selected_building': building,
        'selected_cabinet': cabinet_id,
        'user_name': request.user.username,
    })


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
    building = request.GET.get('building')
    cabinet_id = request.GET.get('cabinet')

    requests = ServiceRequest.objects.filter(
        is_completed=False
    ).filter(
        Q(assigned_engineer=request.user) | Q(assigned_engineer__isnull=True)
    ).select_related('device__cabinet')

    if building:
        requests = requests.filter(device__cabinet__building=building)
    if cabinet_id:
        requests = requests.filter(device__cabinet__id=cabinet_id)

    buildings = Cabinet.objects.values_list('building', flat=True).distinct()
    cabinets = Cabinet.objects.all()

    return render(request, 'core/engineer_dashboard.html', {
        'requests': requests.order_by('-created_at'),
        'user_name': request.user.username,
        'buildings': buildings,
        'cabinets': cabinets,
        'selected_building': building,
        'selected_cabinet': cabinet_id,
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

    # Если заявка приостановлена, блокируем действия инженера
    if service_request.is_paused:
        logs = service_request.service_logs.select_related('engineer').order_by('-action_date')
        context = {
            'request': service_request,
            'logs': logs,
            'replacement_request': replacement_request,
            'paused_message': "Заявка приостановлена и ожидает одобрения администратора.",
        }
        return render(request, 'core/engineer_request_detail.html', context)

    if request.method == 'POST':
        form_log = ServiceLogForm(request.POST)

        if form_log.is_valid():
            log = form_log.save(commit=False)
            log.request = service_request
            log.engineer = request.user
            log.save()

            # Завершение заявки
            if form_log.cleaned_data.get('complete_request'):
                service_request.is_completed = True
                service_request.is_paused = False
                service_request.save()

            # Запрос на замену устройства
            if form_log.cleaned_data.get('replacement_request'):
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

                service_request.requires_replacement = True
                service_request.is_paused = True
                service_request.save()

            return redirect('engineer_request_detail', request_id=request_id)

        # Сохранение отчёта по замене
        elif 'replacement_report' in request.POST and replacement_request and replacement_request.admin_approved:
            form_report = DeviceReplacementReportForm(request.POST)
            if form_report.is_valid():
                try:
                    # Пытаемся получить существующий отчёт для обновления
                    report = DeviceReplacementReport.objects.get(replacement_request=replacement_request)
                    for field, value in form_report.cleaned_data.items():
                        setattr(report, field, value)
                    report.created_by = request.user  # Обновляем создателя, если нужно
                    report.save()
                except DeviceReplacementReport.DoesNotExist:
                    # Создаем новый отчёт, если не существует
                    report = form_report.save(commit=False)
                    report.replacement_request = replacement_request
                    report.created_by = request.user
                    report.save()

                service_request.is_completed = True
                service_request.is_paused = False
                service_request.save()

                messages.success(request, 'Отчёт по замене успешно сохранён и заявка закрыта.')
                return redirect('engineer_request_detail', request_id=request_id)
    else:
        form_log = ServiceLogForm()
        form_report = None

        if replacement_request and replacement_request.admin_approved:
            try:
                report_instance = replacement_request.devicereplacementreport
            except DeviceReplacementReport.DoesNotExist:
                report_instance = None
            form_report = DeviceReplacementReportForm(instance=report_instance)

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
    # Активные (ожидающие одобрения) заявки на замену
    pending_replacements = ReplacementRequest.objects.filter(
        admin_approved=False
    ).select_related(
        'service_request', 'engineer', 'service_request__device'
    ).order_by('-created_at')

    # Завершённые (одобренные) заявки на замену
    approved_replacements = ReplacementRequest.objects.filter(
        admin_approved=True
    ).select_related(
        'service_request', 'engineer', 'service_request__device'
    ).order_by('-approved_at')

    return render(request, 'core/admin_dashboard.html', {
        'pending_replacements': pending_replacements,
        'approved_replacements': approved_replacements,
        'user_name': request.user.username,
    })


@login_required
@admin_required
def replacement_request_detail(request, replacement_id):
    # Получаем запрос на замену, который ещё не одобрен админом
    replacement_request = get_object_or_404(ReplacementRequest, id=replacement_id, admin_approved=False)
    service_request = replacement_request.service_request

    # Получаем логи по связанной сервисной заявке
    logs = ServiceLog.objects.filter(request=service_request).order_by('-action_date')

    # Получаем отчёт по замене, если есть
    try:
        report_instance = DeviceReplacementReport.objects.get(replacement_request=replacement_request)
    except DeviceReplacementReport.DoesNotExist:
        report_instance = None

    if request.method == 'POST':
        form = DeviceReplacementReportForm(request.POST, instance=report_instance)
        if form.is_valid():
            report = form.save(commit=False)
            report.replacement_request = replacement_request
            report.created_by = request.user
            report.save()

            # Добавляем запись в журнал сервиса
            ServiceLog.objects.create(
                request=service_request,
                engineer=request.user,
                action_type="Замена подтверждена",
                notes=(
                    f"Администратор {request.user.username} подтвердил замену. "
                    f"Новое устройство: {report.new_device_name}, "
                    f"Серийный номер: {report.new_device_serial_number}, "
                    f"Стоимость: {report.new_device_cost}."
                )
            )

            # Помечаем запрос как одобренный
            replacement_request.admin_approved = True
            replacement_request.save()

            # Обновляем состояние сервисной заявки
            service_request.requires_replacement = False
            service_request.is_paused = False
            service_request.save()

            messages.success(request, f'Запрос замены №{replacement_request.id} успешно подтвержден.')
            return redirect('admin_dashboard')
    else:
        form = DeviceReplacementReportForm(instance=report_instance)

    return render(request, 'core/replacement_request.html', {
        'replacement_request': replacement_request,
        'service_request': service_request,
        'form': form,
        'logs': logs,
    })

@login_required
@admin_required
def admin_active_requests(request):
    from django.db.models import Q

    # Только активные заявки на обслуживание
    service_requests = ServiceRequest.objects.filter(
        is_completed=False,
        is_paused=False
    ).select_related('device__cabinet').order_by('-created_at')

    # Только замены, где заявка на обслуживание приостановлена, назначен инженер, и она не завершена
    replacement_requests = ReplacementRequest.objects.filter(
        service_request__is_paused=True,
        service_request__assigned_engineer__isnull=False,
        service_request__is_completed=False
    ).select_related('service_request__device__cabinet').order_by('-created_at')

    # Оборачиваем объекты для шаблона
    wrapped_service_requests = [{'obj': r, 'type': 'service_request'} for r in service_requests]
    wrapped_replacement_requests = [{'obj': r, 'type': 'replacement_request'} for r in replacement_requests]

    # Объединяем и сортируем по дате
    all_active_requests = sorted(
        wrapped_service_requests + wrapped_replacement_requests,
        key=lambda x: x['obj'].created_at,
        reverse=True
    )

    return render(request, 'core/admin_active_requests.html', {
        'requests': all_active_requests,
        'user_name': request.user.username,
    })




@login_required
@admin_required
def admin_completed_requests(request):
    # Заявки на замену, которые одобрены админом и имеют отчёт о замене
    completed_requests = ReplacementRequest.objects.filter(
        admin_approved=True,
        devicereplacementreport__isnull=False
    ).select_related('service_request__device__cabinet').order_by('-created_at')

    # Фильтрация по зданию и кабинету
    building = request.GET.get('building')
    cabinet_id = request.GET.get('cabinet')

    if building:
        completed_requests = completed_requests.filter(service_request__device__cabinet__building=building)
    if cabinet_id:
        completed_requests = completed_requests.filter(service_request__device__cabinet__id=cabinet_id)

    buildings = Cabinet.objects.values_list('building', flat=True).distinct()
    cabinets = Cabinet.objects.all()

    return render(request, 'core/admin_completed_requests.html', {
        'requests': completed_requests,
        'buildings': buildings,
        'cabinets': cabinets,
        'selected_building': building,
        'selected_cabinet': cabinet_id,
        'user_name': request.user.username,
    })



@login_required
@admin_required
def admin_request_detail(request, request_id):
    # Получаем сервисную заявку по ID
    service_request = get_object_or_404(ServiceRequest, id=request_id)

    # Получаем логи по заявке через related_name service_logs
    logs = service_request.service_logs.select_related('engineer').order_by('-action_date')

    # Пытаемся получить связанную заявку на замену (если есть)
    replacement_request = ReplacementRequest.objects.filter(service_request=service_request).first()

    report = None
    if replacement_request:
        try:
            report = replacement_request.devicereplacementreport
        except DeviceReplacementReport.DoesNotExist:
            report = None

    context = {
        'request': service_request,
        'logs': logs,
        'replacement_request': replacement_request,
        'replacement_report': report,
    }
    return render(request, 'core/admin_request_detail.html', context)


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


@staff_member_required
def admin_replacement_approval(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    replacement_request = getattr(service_request, 'replacement_request', None)
    
    if not replacement_request:
        # Если запрос на замену не создавался — можно показать ошибку или перенаправить
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = ReplacementApprovalForm(request.POST, instance=replacement_request)
        if form.is_valid():
            replacement = form.save(commit=False)
            replacement.approve()  # вызываем метод approve, который меняет флаги
            replacement.save()
            
            # Переводим заявку в завершённые — или даём возможность инженеру работать дальше
            service_request.is_completed = False
            service_request.is_paused = False
            service_request.save()
            
            return redirect('admin_replacement_approval', request_id=request_id)
    else:
        form = ReplacementApprovalForm(instance=replacement_request)

    context = {
        'request': service_request,
        'replacement_request': replacement_request,
        'form': form,
    }
    return render(request, 'core/admin_replacement_approval.html', context)

@login_required
def teacher_dashboard(request):
    return render(request, 'core/teacher_dashboard.html', {'user': request.user})



@login_required
@engineer_required
def all_active_requests(request):
    qs = ServiceRequest.objects.select_related('device__cabinet', 'assigned_engineer').all()

    # Параметры фильтрации из GET-запроса
    building = request.GET.get('building')
    cabinet_id = request.GET.get('cabinet')
    engineer_id = request.GET.get('engineer')
    status = request.GET.get('status')
    date = request.GET.get('date')

    # Применение фильтров
    if building:
        qs = qs.filter(device__cabinet__building=building)
    if cabinet_id:
        qs = qs.filter(device__cabinet__id=cabinet_id)
    if engineer_id:
        qs = qs.filter(assigned_engineer__id=engineer_id)

    if status == 'new':
        qs = qs.filter(assigned_engineer__isnull=True, is_paused=False)
    elif status == 'in_progress':
        qs = qs.filter(assigned_engineer__isnull=False, is_paused=False)
    elif status == 'paused':
        qs = qs.filter(is_paused=True)
    elif status == 'completed':
        qs = qs.filter(is_completed=True)

    if date:
        qs = qs.filter(created_at__date=date)

    # Данные для выпадающих списков
    buildings = Cabinet.objects.values_list('building', flat=True).distinct()
    cabinets = Cabinet.objects.all()
    engineers = (
        ServiceRequest.objects.filter(assigned_engineer__isnull=False)
        .values('assigned_engineer__id', 'assigned_engineer__username')
        .distinct()
    )

    return render(request, 'engineer/all_active_requests.html', {
        'requests': qs.order_by('-created_at'),
        'buildings': buildings,
        'cabinets': cabinets,
        'engineers': engineers,
        'selected_building': building,
        'selected_cabinet': cabinet_id,
        'selected_engineer': engineer_id,
        'selected_status': status,
        'selected_date': date,
        'title': 'Все активные заявки',
    })



from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from .models import ServiceRequest, Cabinet

@login_required
@engineer_required
def my_active_requests(request):
    user = request.user
    requests_qs = ServiceRequest.objects.filter(assigned_engineer=user)

    # Фильтрация
    building = request.GET.get("building")
    cabinet_id = request.GET.get("cabinet")
    status = request.GET.get("status")
    from_date = parse_date(request.GET.get("from_date") or "")
    to_date = parse_date(request.GET.get("to_date") or "")

    if building:
        requests_qs = requests_qs.filter(device__cabinet__building=building)

    if cabinet_id:
        requests_qs = requests_qs.filter(device__cabinet__id=cabinet_id)

    if status == "completed":
        requests_qs = requests_qs.filter(is_completed=True)
    elif status == "paused":
        requests_qs = requests_qs.filter(is_paused=True)
    elif status == "active":
        requests_qs = requests_qs.filter(is_completed=False, is_paused=False)

    if from_date:
        requests_qs = requests_qs.filter(created_at__date__gte=from_date)
    if to_date:
        requests_qs = requests_qs.filter(created_at__date__lte=to_date)

    # Сортировка от новых к старым
    requests_qs = requests_qs.order_by('-created_at')

    buildings = Cabinet.objects.values_list("building", flat=True).distinct()
    cabinets = Cabinet.objects.all()

    return render(request, "engineer/my_active_requests.html", {
        "requests": requests_qs,
        "buildings": buildings,
        "cabinets": cabinets,
    })





@login_required
@engineer_required
def completed_requests(request):
    qs = ServiceRequest.objects.filter(
        is_completed=True
    ).select_related('device__cabinet').order_by('-created_at')

    building = request.GET.get('building')
    cabinet_id = request.GET.get('cabinet')

    if building:
        qs = qs.filter(device__cabinet__building=building)
    if cabinet_id:
        qs = qs.filter(device__cabinet__id=cabinet_id)

    buildings = Cabinet.objects.values_list('building', flat=True).distinct()
    cabinets = Cabinet.objects.all()

    return render(request, 'engineer/completed_requests.html', {
        'requests': qs,
        'buildings': buildings,
        'cabinets': cabinets,
        'selected_building': building,
        'selected_cabinet': cabinet_id,
        'title': 'Завершённые заявки',
    })

@login_required
@engineer_required
def assign_request_from_all(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id, assigned_engineer__isnull=True)
    service_request.assigned_engineer = request.user
    service_request.save()
    messages.success(request, f'Вы взяли заявку #{service_request.id} в работу.')
    return redirect('all_active_requests')
