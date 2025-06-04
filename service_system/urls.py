from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Пути из core.urls на корне
    # path('accounts/', include('django.contrib.auth.urls')),  # Убираем эту строку
]
