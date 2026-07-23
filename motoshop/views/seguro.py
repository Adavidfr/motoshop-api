# motoshop/views/seguro.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Seguro
from motoshop.serializers.seguro import SeguroSerializer, SeguroCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import SeguroFilter
from motoshop.permissions import filter_queryset_by_venta_owner


class SeguroViewSet(viewsets.ModelViewSet):
    """
    Seguros: lectura filtrada para clientes, gestión completa para administradores.
    """
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = SeguroFilter
    search_fields      = ['aseguradora', 'numero_poliza', 'tipo_cobertura']
    ordering_fields    = ['id_seguro', 'fecha_inicio', 'fecha_fin', 'costo_anual']
    ordering           = ['-fecha_inicio']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = Seguro.objects.select_related(
            'id_venta', 'id_venta__id_usuario_cliente',
        ).all()
        return filter_queryset_by_venta_owner(qs, self.request.user)

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return SeguroCreateSerializer
        return SeguroSerializer
