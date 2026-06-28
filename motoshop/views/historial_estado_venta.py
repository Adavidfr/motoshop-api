# motoshop/views/historial_estado_venta.py
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import HistorialEstadoVenta
from motoshop.serializers.historial_estado_venta import (
    HistorialEstadoVentaSerializer,
    HistorialEstadoVentaCreateSerializer,
)
from motoshop.pagination import StandardPagination
from motoshop.filters import HistorialEstadoVentaFilter


class HistorialEstadoVentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD del historial de estados de venta.
    Solo accesible para staff/admin.

    Endpoints generados:
      GET    /historial-estado-venta/          → listar todos
      POST   /historial-estado-venta/          → registrar cambio
      GET    /historial-estado-venta/<id>/     → detalle
      PATCH  /historial-estado-venta/<id>/     → editar
      DELETE /historial-estado-venta/<id>/     → eliminar

    Filtros disponibles:
      ?id_venta=<id>
      ?estado_nuevo=<estado>
    """
    permission_classes = [IsAdminUser]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = HistorialEstadoVentaFilter
    search_fields      = ['estado_anterior', 'estado_nuevo', 'observacion']
    ordering_fields    = ['id_historial', 'fecha_cambio']
    ordering           = ['-fecha_cambio']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return HistorialEstadoVenta.objects.select_related('id_venta').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return HistorialEstadoVentaCreateSerializer
        return HistorialEstadoVentaSerializer
