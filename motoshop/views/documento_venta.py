# motoshop/views/documento_venta.py
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import DocumentoVenta
from motoshop.serializers.documento_venta import DocumentoVentaSerializer, DocumentoVentaCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import DocumentoVentaFilter


class DocumentoVentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de documentos de venta.
    Solo accesible para staff/admin.

    Endpoints generados:
      GET    /documentos-venta/          → listar todos
      POST   /documentos-venta/          → subir documento
      GET    /documentos-venta/<id>/     → detalle
      PATCH  /documentos-venta/<id>/     → editar
      DELETE /documentos-venta/<id>/     → eliminar

    Filtros disponibles:
      ?id_venta=<id>
      ?tipo_documento=<tipo>
    """
    permission_classes = [IsAdminUser]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = DocumentoVentaFilter
    search_fields      = ['tipo_documento', 'archivo_url']
    ordering_fields    = ['id_documento', 'fecha_subida']
    ordering           = ['-fecha_subida']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return DocumentoVenta.objects.select_related('id_venta').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentoVentaCreateSerializer
        return DocumentoVentaSerializer
