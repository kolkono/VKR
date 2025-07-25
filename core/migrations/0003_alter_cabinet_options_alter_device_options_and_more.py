# Generated by Django 5.2.1 on 2025-06-04 02:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_cabinet_device_servicerequest_servicelog'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cabinet',
            options={'verbose_name': 'Кабинет', 'verbose_name_plural': 'Кабинеты'},
        ),
        migrations.AlterModelOptions(
            name='device',
            options={'verbose_name': 'Устройство', 'verbose_name_plural': 'Устройства'},
        ),
        migrations.AlterModelOptions(
            name='servicelog',
            options={'verbose_name': 'Журнал обслуживания', 'verbose_name_plural': 'Журналы обслуживания'},
        ),
        migrations.AlterModelOptions(
            name='servicerequest',
            options={'verbose_name': 'Заявка на обслуживание', 'verbose_name_plural': 'Заявки на обслуживание'},
        ),
        migrations.AlterField(
            model_name='cabinet',
            name='building',
            field=models.CharField(max_length=50, verbose_name='Корпус'),
        ),
        migrations.AlterField(
            model_name='cabinet',
            name='number',
            field=models.CharField(max_length=10, verbose_name='Номер кабинета'),
        ),
        migrations.AlterField(
            model_name='device',
            name='cabinet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='core.cabinet', verbose_name='Кабинет'),
        ),
        migrations.AlterField(
            model_name='device',
            name='cost',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Стоимость'),
        ),
        migrations.AlterField(
            model_name='device',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Название устройства'),
        ),
        migrations.AlterField(
            model_name='device',
            name='purchase_date',
            field=models.DateField(verbose_name='Дата покупки'),
        ),
        migrations.AlterField(
            model_name='device',
            name='serial_number',
            field=models.CharField(max_length=100, unique=True, verbose_name='Серийный номер'),
        ),
        migrations.AlterField(
            model_name='servicelog',
            name='action_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата действия'),
        ),
        migrations.AlterField(
            model_name='servicelog',
            name='action_type',
            field=models.CharField(max_length=50, verbose_name='Тип действия'),
        ),
        migrations.AlterField(
            model_name='servicelog',
            name='cost',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Стоимость работы'),
        ),
        migrations.AlterField(
            model_name='servicelog',
            name='engineer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='service_logs', to=settings.AUTH_USER_MODEL, verbose_name='Инженер'),
        ),
        migrations.AlterField(
            model_name='servicelog',
            name='notes',
            field=models.TextField(blank=True, verbose_name='Примечания'),
        ),
        migrations.AlterField(
            model_name='servicelog',
            name='request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_logs', to='core.servicerequest', verbose_name='Заявка'),
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='assigned_engineer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_requests', to=settings.AUTH_USER_MODEL, verbose_name='Инженер'),
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата создания'),
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requests_created', to=settings.AUTH_USER_MODEL, verbose_name='Создал'),
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='description',
            field=models.TextField(verbose_name='Описание проблемы'),
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_requests', to='core.device', verbose_name='Устройство'),
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='is_completed',
            field=models.BooleanField(default=False, verbose_name='Завершено'),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(blank=True, choices=[('admin', 'Администратор'), ('engineer', 'Инженер'), ('teacher', 'Преподаватель')], max_length=20, null=True),
        ),
        migrations.CreateModel(
            name='ReplacementRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField(blank=True, verbose_name='Причина замены')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('admin_approved', models.BooleanField(default=False, verbose_name='Одобрено администратором')),
                ('engineer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('service_request', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='replacement_request', to='core.servicerequest')),
            ],
            options={
                'verbose_name': 'Запрос на замену устройства',
                'verbose_name_plural': 'Запросы на замену устройств',
            },
        ),
        migrations.CreateModel(
            name='DeviceReplacementReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_device_info', models.TextField(verbose_name='Информация о списанном устройстве')),
                ('new_device_name', models.CharField(max_length=100, verbose_name='Название нового устройства')),
                ('new_device_cost', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Стоимость нового устройства')),
                ('new_device_serial_number', models.CharField(max_length=100, verbose_name='Серийный номер нового устройства')),
                ('notes', models.TextField(blank=True, verbose_name='Примечания')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('replacement_request', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='core.replacementrequest')),
            ],
            options={
                'verbose_name': 'Отчёт по замене устройства',
                'verbose_name_plural': 'Отчёты по замене устройств',
            },
        ),
    ]
