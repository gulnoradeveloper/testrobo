"""Rolga asoslangan ruxsatlar (RBAC) — web view'lar uchun."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles, allow_admin=True):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            user = request.user
            if user.role in roles or (allow_admin and user.is_admin_role):
                return view(request, *args, **kwargs)
            raise PermissionDenied("Bu sahifa sizning rolingiz uchun mavjud emas.")

        return wrapped

    return decorator


def admin_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_admin_role:
            raise PermissionDenied("Faqat administrator uchun.")
        return view(request, *args, **kwargs)

    return wrapped
