from django.http import HttpResponseForbidden
from functools import wraps

def role_required(required_role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role == required_role:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Доступ запрещён: недостаточно прав")
        return _wrapped_view
    return decorator

# Для удобства, готовые декораторы
teacher_required = role_required('teacher')
engineer_required = role_required('engineer')
admin_required = role_required('admin')
