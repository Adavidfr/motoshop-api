# motoshop/views/historial_estado_venta.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import HistorialEstadoVenta
from motoshop.serializers.historial_estado_venta import HistorialEstadoVentaSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import HistorialEstadoVentaFilter
from motoshop.permissions import filter_queryset_by_venta_owner


class HistorialEstadoVentaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Historial append-only: solo lectura.
    Generado automáticamente por los Services; no editable vía API.
    """
    serializer_class   = HistorialEstadoVentaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = HistorialEstadoVentaFilter
    search_fields      = ['estado_anterior', 'estado_nuevo', 'observacion']
    ordering_fields    = ['id_historial', 'fecha_cambio']
    ordering           = ['-fecha_cambio']

    def get_queryset(self):
        qs = HistorialEstadoVenta.objects.select_related(
            'id_venta', 'id_venta__id_usuario_cliente', 'id_usuario',
        ).all()
        return filter_queryset_by_venta_owner(qs, self.request.user, venta_field='id_venta')
