from django import forms
from .models import ServiceRequest, ServiceLog, ReplacementRequest, DeviceReplacementReport

class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['device', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'device': 'Устройство',
            'description': 'Описание проблемы',
        }

class ServiceLogForm(forms.ModelForm):
    complete_request = forms.BooleanField(required=False, label="Завершить заявку")

    class Meta:
        model = ServiceLog
        fields = ['action_type', 'notes']  # обязательно поле note
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Введите примечание...'}),
            'action_type': forms.TextInput(attrs={'placeholder': 'Тип действия'}),
        }
        


class ReplacementRequestForm(forms.ModelForm):
    class Meta:
        model = ReplacementRequest
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'reason': 'Причина замены',
        }


class DeviceReplacementReportForm(forms.ModelForm):
    class Meta:
        model = DeviceReplacementReport
        fields = ['old_device_info', 'new_device_name', 'new_device_cost', 'new_device_serial_number', 'notes']
        widgets = {
            'old_device_info': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'new_device_cost': forms.NumberInput(attrs={'step': '0.01'}),
        }
        labels = {
            'old_device_info': 'Информация о списанном устройстве',
            'new_device_name': 'Название нового устройства',
            'new_device_cost': 'Стоимость нового устройства',
            'new_device_serial_number': 'Серийный номер нового устройства',
            'notes': 'Примечания',
        }
