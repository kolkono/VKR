from django import forms
from .models import ServiceRequest, ServiceLog, ReplacementRequest, DeviceReplacementReport
from .models import Cabinet, Device


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
        
        


class AdminDeviceReplacementForm(forms.Form):
    from_cabinet_for_new = forms.ModelChoiceField(
        queryset=Cabinet.objects.all(),
        label="Откуда переместить новое устройство",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_from_cabinet'  # если нужна динамика через JS
        })
    )

    new_device = forms.ModelChoiceField(
        queryset=Device.objects.none(),  # Заполняется динамически по выбору кабинета (если нужно)
        label="Новое устройство (на замену)",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_new_device'
        })
    )

    to_cabinet_for_old = forms.ModelChoiceField(
        queryset=Cabinet.objects.all(),
        label="Куда переместить старое устройство",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_to_cabinet'
        })
    )

    notes = forms.CharField(
        label="Примечания",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Опишите причину и детали замены...'
        })
    )