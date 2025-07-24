from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                login_url = getattr(settings, 'LOGIN_URL', '/accounts/login/')
                return redirect(f'{login_url}?next={request.path}')

            if request.user.role not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def admin_required(view_func):
    decorated_view = role_required(allowed_roles=['ADMIN'])(view_func)
    return decorated_view

def bientapvien_required(view_func):
    decorated_view = role_required(allowed_roles=['BIENTAPVIEN', 'ADMIN'])(view_func)
    return decorated_view

def tacgia_required(view_func):
    decorated_view = role_required(allowed_roles=['TACGIA', 'ADMIN'])(view_func)
    return decorated_view

def admin_or_bientapvien_required(view_func):
    decorated_view = role_required(allowed_roles=['ADMIN', 'BIENTAPVIEN'])(view_func)
    return decorated_view

def bientapvien_required(view_func):
    decorated_view = role_required(allowed_roles=['ADMIN', 'BIENTAPVIEN'])(view_func)
    return decorated_view