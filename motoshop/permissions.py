"""
motoshop/permissions.py
-----------------------
Custom permission classes based on Django Groups.

Grupos disponibles: admin, usuario, cliente, vendedor
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


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
    Lectura libre para todos, escritura solo para admin.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            request.user.is_superuser or _user_in_group(request.user, 'admin')
        )


class IsStaffOrReadOnly(BasePermission):
    """Lectura para autenticados, escritura solo para staff. (Etapa 5)"""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_staff)


class IsOwnerOrStaff(BasePermission):
    """El propietario del pedido o staff pueden acceder. (Etapa 5)"""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff
