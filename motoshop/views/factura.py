# motoshop/views/factura.py
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Factura
from motoshop.serializers.factura import FacturaSerializer, FacturaCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import FacturaFilter


class FacturaViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de facturas.
    Solo accesible para staff/admin.

    Endpoints generados:
      GET    /facturas/          → listar todas
      POST   /facturas/          → emitir factura
      GET    /facturas/<id>/     → detalle
      PATCH  /facturas/<id>/     → editar
      DELETE /facturas/<id>/     → eliminar

    Filtros disponibles:
      ?id_venta=<id>
      ?numero_factura=<número>
    """
    permission_classes = [IsAdminUser]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = FacturaFilter
    search_fields      = ['numero_factura']
    ordering_fields    = ['id_factura', 'fecha_emision', 'total']
    ordering           = ['-fecha_emision']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Factura.objects.select_related('id_venta').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return FacturaCreateSerializer
        return FacturaSerializer
