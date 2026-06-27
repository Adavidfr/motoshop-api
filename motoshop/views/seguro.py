# motoshop/views/seguro.py
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Seguro
from motoshop.serializers.seguro import SeguroSerializer, SeguroCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import SeguroFilter


class SeguroViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de seguros.
    Solo accesible para staff/admin.

    Endpoints generados:
      GET    /seguros/          → listar todos
      POST   /seguros/          → registrar seguro
      GET    /seguros/<id>/     → detalle
      PATCH  /seguros/<id>/     → editar
      DELETE /seguros/<id>/     → eliminar

    Filtros disponibles:
      ?estado=activo
      ?id_venta=<id>
      ?aseguradora=<nombre>
    """
    permission_classes = [IsAdminUser]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = SeguroFilter
    search_fields      = ['aseguradora', 'numero_poliza', 'tipo_cobertura']
    ordering_fields    = ['id_seguro', 'fecha_inicio', 'fecha_fin', 'costo_anual']
    ordering           = ['-fecha_inicio']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Seguro.objects.select_related('id_venta').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return SeguroCreateSerializer
        return SeguroSerializer
