# motoshop/views/garantia.py
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Garantia
from motoshop.serializers.garantia import GarantiaSerializer, GarantiaCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import GarantiaFilter


class GarantiaViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de garantías.
    Solo accesible para staff/admin.

    Endpoints generados:
      GET    /garantias/          → listar todas
      POST   /garantias/          → registrar garantía
      GET    /garantias/<id>/     → detalle
      PATCH  /garantias/<id>/     → editar
      DELETE /garantias/<id>/     → eliminar

    Filtros disponibles:
      ?estado=activa
      ?id_venta=<id>
    """
    permission_classes = [IsAdminUser]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = GarantiaFilter
    search_fields      = ['descripcion']
    ordering_fields    = ['id_garantia', 'fecha_inicio', 'fecha_fin', 'meses_garantia']
    ordering           = ['-fecha_inicio']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Garantia.objects.select_related('id_venta').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return GarantiaCreateSerializer
        return GarantiaSerializer
