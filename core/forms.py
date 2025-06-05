from django import forms
from .models import ServiceRequest, ServiceLog, ReplacementRequest, DeviceReplacementReport

class ServiceRequestForm(forms.ModelForm):
    replacement_requested = forms.BooleanField(
        required=False,
        label="Отправить запрос на замену оборудования"
    )

    class Meta:
        model = ServiceRequest
        fields = ['device', 'description', 'replacement_requested']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'device': 'Устройство',
            'description': 'Описание проблемы',
        }

class ServiceLogForm(forms.ModelForm):
    complete_request = forms.BooleanField(
        required=False,
        label="Завершить заявку"
    )
    replacement_request = forms.BooleanField(
        required=False,
        label="Отправить запрос на замену оборудования"
    )

    class Meta:
        model = ServiceLog
        fields = ['action_type', 'notes']  # обязательно поле notes
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
        fields = ['device', 'from_cabinet', 'to_cabinet', 'notes']
        widgets = {
            'device': forms.Select(attrs={'class': 'form-select'}),
            'from_cabinet': forms.Select(attrs={'class': 'form-select'}),
            'to_cabinet': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control'}),
        }