from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Главная и профиль
    path('', views.home, name='home'),
    path('profile/', views.profile_view, name='profile'),

    # Преподаватель
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('create-request/', views.create_request, name='create_request'),

    # Инженер
    path('engineer/dashboard/', views.engineer_dashboard, name='engineer_dashboard'),
    path('engineer/all-active/', views.all_active_requests, name='all_active_requests'),
    path('engineer/my-active/', views.my_active_requests, name='my_active_requests'),
    path('engineer/request/<int:request_id>/assign-from-all/', views.assign_request_from_all, name='assign_request_from_all'),
    path('engineer/request/<int:request_id>/', views.engineer_request_detail, name='engineer_request_detail'),
    path('engineer/request/<int:request_id>/assign/', views.assign_request_to_self, name='assign_request_to_self'),
    path('active-requests/', views.active_requests, name='active_requests'),
    path('completed-requests/', views.completed_requests, name='completed_requests'),
    

    # Админка — единый префикс /dashboard/admin/
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/replacement/<int:replacement_id>/', views.replacement_request_detail, name='replacement_request_detail'),
    path('dashboard/admin/request/<int:request_id>/', views.admin_request_detail, name='admin_request_detail'),
    path('dashboard/admin/replacement-requests/', views.admin_replacement_requests, name='admin_replacement_requests'),
    path('dashboard/admin/replacement-requests/<int:request_id>/approve/', views.admin_approve_replacement, name='admin_approve_replacement'),
    path('dashboard/admin/replacement-requests/<int:request_id>/reject/', views.admin_reject_replacement, name='admin_reject_replacement'),

    # Новые маршруты для активных и завершённых заявок админа
    path('dashboard/admin/active/', views.admin_active_requests, name='admin_active_requests'),
    path('dashboard/admin/completed/', views.admin_completed_requests, name='admin_completed_requests'),

    # API
    path('api/devices/', views.devices_api, name='devices_api'),

    # Аутентификация
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
