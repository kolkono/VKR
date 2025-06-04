from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Преподаватель
    path('my-requests/', views.my_requests, name='my_requests'),
    path('create-request/', views.create_request, name='create_request'),

    # Инженер
    path('engineer/dashboard/', views.engineer_dashboard, name='engineer_dashboard'),
    path('engineer/request/<int:request_id>/', views.engineer_request_detail, name='engineer_request_detail'),

    # Админка (пользовательская, не Django admin)
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/replacement/<int:replacement_id>/', views.replacement_request_detail, name='replacement_request_detail'),

    # API
    path('api/devices/', views.devices_api, name='devices_api'),

    # Аутентификация
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
