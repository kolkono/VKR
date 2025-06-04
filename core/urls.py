from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile_view, name='profile'),

    # Преподаватель
    path('my-requests/', views.my_requests, name='my_requests'),
    path('create-request/', views.create_request, name='create_request'),

    # Инженер
    path('engineer/dashboard/', views.engineer_dashboard, name='engineer_dashboard'),
    path('engineer/request/<int:request_id>/', views.engineer_request_detail, name='engineer_request_detail'),
    path('engineer/request/<int:request_id>/assign/', views.assign_request_to_self, name='assign_request_to_self'),
    path('active-requests/', views.active_requests, name='active_requests'),
    path('completed-requests/', views.completed_requests, name='completed_requests'),

    # Админка (пользовательская, не Django admin)
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/replacement/<int:replacement_id>/', views.replacement_request_detail, name='replacement_request_detail'),

    # API
    path('api/devices/', views.devices_api, name='devices_api'),

    # Аутентификация
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('admin-panel/replacement-requests/', views.admin_replacement_requests, name='admin_replacement_requests'),
    path('admin-panel/replacement-requests/<int:request_id>/approve/', views.admin_approve_replacement, name='admin_approve_replacement'),
    path('admin-panel/replacement-requests/<int:request_id>/reject/', views.admin_reject_replacement, name='admin_reject_replacement'),
]
