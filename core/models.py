from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('engineer', 'Инженер'),
        ('teacher', 'Преподаватель'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)


class Cabinet(models.Model):
    number = models.CharField("Номер кабинета", max_length=10)
    building = models.CharField("Корпус", max_length=50)

    class Meta:
        verbose_name = "Кабинет"
        verbose_name_plural = "Кабинеты"

    def __str__(self):
        return f'{self.building} - {self.number}'


class Device(models.Model):
    cabinet = models.ForeignKey(Cabinet, on_delete=models.CASCADE, related_name='devices', verbose_name="Кабинет")
    name = models.CharField("Название устройства", max_length=100)
    serial_number = models.CharField("Серийный номер", max_length=100, unique=True)
    purchase_date = models.DateField("Дата покупки")
    cost = models.DecimalField("Стоимость", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Устройство"
        verbose_name_plural = "Устройства"

    def __str__(self):
        return f'{self.name} ({self.serial_number})'


class ServiceRequest(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='service_requests', verbose_name="Устройство")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='requests_created', verbose_name="Создал"
    )
    assigned_engineer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_requests', verbose_name="Инженер"
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    description = models.TextField("Описание проблемы")
    is_completed = models.BooleanField("Завершено", default=False)
    requires_replacement = models.BooleanField("Требуется замена", default=False)
    is_paused = models.BooleanField("Приостановлена (ожидание замены)", default=False)

    replacement_requested = models.BooleanField("Запрос на замену оборудования", default=False)

    class Meta:
        verbose_name = "Заявка на обслуживание"
        verbose_name_plural = "Заявки на обслуживание"

    def __str__(self):
        return f'Заявка #{self.id} на {self.device.name}'

    @property
    def status(self):
        if self.is_completed:
            return "Завершена"
        if self.is_paused:
            return "Приостановлена (ожидание замены)"
        return "В процессе"


class ServiceLog(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='service_logs', verbose_name="Заявка")
    engineer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='service_logs', verbose_name="Инженер"
    )
    action_date = models.DateTimeField("Дата действия", auto_now_add=True)
    action_type = models.CharField("Тип действия", max_length=50)  # установка, диагностика, ремонт
    notes = models.TextField("Примечания", blank=True)
    cost = models.DecimalField("Стоимость работы", max_digits=10, decimal_places=2, default=0.0)

    class Meta:
        verbose_name = "Журнал обслуживания"
        verbose_name_plural = "Журналы обслуживания"

    def __str__(self):
        return f'{self.action_type} - {self.action_date.strftime("%d.%m.%Y")} (Заявка #{self.request.id})'


class ReplacementRequest(models.Model):
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name='replacement_request')
    engineer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.TextField("Причина замены", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Новые поля ↓↓↓
    new_device_model = models.CharField("Модель нового устройства", max_length=255, blank=True, null=True)
    new_device_serial = models.CharField("Серийный номер нового устройства", max_length=255, blank=True, null=True)
    admin_approved = models.BooleanField("Одобрено администратором", default=False)
    approved_at = models.DateTimeField("Дата одобрения", blank=True, null=True)

    def approve(self):
        self.admin_approved = True
        self.approved_at = timezone.now()
        self.save()

        # Возобновляем работу инженера
        self.service_request.is_paused = False
        self.service_request.save()

    class Meta:
        verbose_name = "Запрос на замену устройства"
        verbose_name_plural = "Запросы на замену устройств"

    def __str__(self):
        return f"Запрос на замену для заявки #{self.service_request.id}"


class DeviceReplacementReport(models.Model):
    replacement_request = models.OneToOneField(ReplacementRequest, on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    old_device_info = models.TextField("Информация о списанном устройстве")
    new_device_name = models.CharField("Название нового устройства", max_length=100)
    new_device_cost = models.DecimalField("Стоимость нового устройства", max_digits=10, decimal_places=2)
    new_device_serial_number = models.CharField("Серийный номер нового устройства", max_length=100)
    notes = models.TextField("Примечания", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отчёт по замене устройства"
        verbose_name_plural = "Отчёты по замене устройств"

    def __str__(self):
        return f"Отчёт по замене (Запрос #{self.replacement_request.id})"
