from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Cabinet, Device, ServiceRequest, ServiceLog


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Роль", {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role_display', 'is_staff')
    list_display_links = ('username',)
    verbose_name = 'Пользователь'
    verbose_name_plural = 'Пользователи'

    def get_role_display(self, obj):
        return dict(User.ROLE_CHOICES).get(obj.role, 'Неизвестно')
    get_role_display.short_description = 'Роль'


admin.site.register(User, CustomUserAdmin)


@admin.register(Cabinet)
class CabinetAdmin(admin.ModelAdmin):
    list_display = ('building', 'number')
    search_fields = ('building', 'number')
    verbose_name = 'Кабинет'
    verbose_name_plural = 'Кабинеты'


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'serial_number', 'cabinet', 'purchase_date', 'cost')
    list_filter = ('cabinet',)
    search_fields = ('name', 'serial_number')
    verbose_name = 'Устройство'
    verbose_name_plural = 'Устройства'


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'device', 'created_by', 'assigned_engineer', 'created_at', 'is_completed')
    list_filter = ('is_completed', 'created_at')
    search_fields = ('device__name', 'created_by__username', 'assigned_engineer__username')
    verbose_name = 'Заявка'
    verbose_name_plural = 'Заявки'


@admin.register(ServiceLog)
class ServiceLogAdmin(admin.ModelAdmin):
    list_display = ('request', 'engineer', 'action_type', 'action_date', 'cost')
    list_filter = ('action_type', 'action_date')
    verbose_name = 'Журнал обслуживания'
    verbose_name_plural = 'Журналы обслуживания'
