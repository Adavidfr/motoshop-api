"""
motoshop/permissions.py
-----------------------
Custom permission classes based on Django Groups.

Grupos disponibles: admin, usuario, cliente, vendedor
"""

from rest_framework.permissions import BasePermission


def _user_in_group(user, group_name: str) -> bool:
    """Helper: verifica si el usuario pertenece a un grupo."""
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


class IsAdmin(BasePermission):
    """Solo usuarios del grupo 'admin' (o is_superuser)."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser or _user_in_group(request.user, 'admin')
        )


class IsUsuario(BasePermission):
    """Solo usuarios del grupo 'usuario'."""

    def has_permission(self, request, view):
        return _user_in_group(request.user, 'usuario')


class IsCliente(BasePermission):
    """Solo usuarios del grupo 'cliente'."""

    def has_permission(self, request, view):
        return _user_in_group(request.user, 'cliente')


class IsVendedor(BasePermission):
    """Solo usuarios del grupo 'vendedor'."""

    def has_permission(self, request, view):
        return _user_in_group(request.user, 'vendedor')


class IsAdminOrVendedor(BasePermission):
    """Admin o vendedor pueden actuar."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser
            or _user_in_group(request.user, 'admin')
            or _user_in_group(request.user, 'vendedor')
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Lectura libre para autenticados, escritura solo para admin.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or _user_in_group(request.user, 'admin')
