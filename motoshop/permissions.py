"""
motoshop/permissions.py
-----------------------
Custom permission classes based on Django staff flags and groups.

Roles funcionales: administrador (is_staff) y cliente (no staff).
Los grupos legacy en auth_group ya no determinan permisos de escritura.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


def _is_administrator(user) -> bool:
    """Helper: usuario con privilegios administrativos."""
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def _user_in_group(user, group_name: str) -> bool:
    """Helper: verifica si el usuario pertenece a un grupo."""
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


class IsAdmin(BasePermission):
    """Solo usuarios administrativos (is_staff o is_superuser)."""

    def has_permission(self, request, view):
        return _is_administrator(request.user)


class IsUsuario(BasePermission):
    """Solo usuarios del grupo 'usuario'."""

    def has_permission(self, request, view):
        return _user_in_group(request.user, 'usuario')


class IsCliente(BasePermission):
    """Solo usuarios del grupo 'cliente'."""

    def has_permission(self, request, view):
        return _user_in_group(request.user, 'cliente')


class IsClientWriteOrStaffReadOnly(BasePermission):
    """
    Lectura para cualquier usuario autenticado (incluido staff).
    Escritura solo para clientes (usuarios no staff).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return not request.user.is_staff


class IsAdminOrReadOnly(BasePermission):
    """
    Lectura libre para todos, escritura solo para administradores (is_staff).
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return _is_administrator(request.user)


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


def filter_queryset_by_venta_owner(queryset, user, venta_field='id_venta'):
    """Filtra registros postventa al cliente propietario de la venta."""
    if user.is_staff:
        return queryset
    return queryset.filter(**{f'{venta_field}__id_usuario_cliente': user})
