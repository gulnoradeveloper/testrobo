from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class HasRole(BasePermission):
    roles = ()
    allow_admin = True

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.role in self.roles or (self.allow_admin and u.is_admin_role)))


def role_permission(*roles, allow_admin=True):
    return type("RolePermission", (HasRole,), {"roles": roles, "allow_admin": allow_admin})


IsProvider = role_permission(User.Role.PROVIDER, allow_admin=False)
IsMahalla = role_permission(User.Role.MAHALLA, allow_admin=False)
IsPsychologist = role_permission(User.Role.PSYCHOLOGIST, allow_admin=False)
IsAdminRole = role_permission(User.Role.ADMIN)
CanOrder = role_permission(User.Role.CUSTOMER, User.Role.PROVIDER, allow_admin=False)
