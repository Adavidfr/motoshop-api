# motoshop/views/documento_venta.py

from django.http import FileResponse

from rest_framework import viewsets, status

from rest_framework.decorators import action

from rest_framework.parsers import FormParser, MultiPartParser

from rest_framework.permissions import IsAuthenticated, IsAdminUser

from rest_framework.response import Response

from rest_framework.filters import SearchFilter, OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend



from motoshop.models import DocumentoVenta

from motoshop.serializers.documento_venta import (

    DocumentoVentaSerializer,

    DocumentoVentaCreateSerializer,

)

from motoshop.pagination import StandardPagination

from motoshop.filters import DocumentoVentaFilter

from motoshop.permissions import filter_queryset_by_venta_owner

from motoshop.services import BusinessError, DocumentoVentaService

from motoshop.utils.api import respuesta_error_servicio





class DocumentoVentaViewSet(viewsets.ModelViewSet):

    """Documentos de venta con archivos reales vía DocumentoVentaService."""

    permission_classes = [IsAuthenticated]

    pagination_class   = StandardPagination

    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_class    = DocumentoVentaFilter

    search_fields      = ['tipo_documento', 'nombre_original']

    ordering_fields    = ['id_documento', 'fecha_subida']

    ordering           = ['-fecha_subida']

    http_method_names  = ['get', 'post', 'delete', 'head', 'options']

    parser_classes     = [MultiPartParser, FormParser]



    def get_queryset(self):

        qs = DocumentoVenta.objects.select_related(

            'id_venta', 'id_venta__id_usuario_cliente', 'subido_por',

        ).all()

        return filter_queryset_by_venta_owner(qs, self.request.user)



    def get_permissions(self):

        if self.action in ('create', 'destroy', 'partial_update', 'update'):

            return [IsAdminUser()]

        return [IsAuthenticated()]



    def get_serializer_class(self):

        if self.action == 'create':

            return DocumentoVentaCreateSerializer

        return DocumentoVentaSerializer



    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:

            documento = DocumentoVentaService.subir(

                data['id_venta'],

                data['tipo_documento'],

                data['archivo'],

                request.user,

            )

        except BusinessError as exc:

            return respuesta_error_servicio(exc)

        return Response(DocumentoVentaSerializer(documento).data, status=status.HTTP_201_CREATED)



    def destroy(self, request, *args, **kwargs):

        documento = self.get_object()

        DocumentoVentaService.eliminar(documento)

        return Response(status=status.HTTP_204_NO_CONTENT)



    @action(detail=True, methods=['get'], url_path='archivo')

    def archivo(self, request, pk=None):

        documento = self.get_object()

        if not DocumentoVentaService.puede_descargar(documento, request.user):

            return Response(

                {'error': 'No tienes permiso para descargar este documento.'},

                status=status.HTTP_403_FORBIDDEN,

            )

        try:
            return DocumentoVentaService.obtener_respuesta_descarga(documento)
        except BusinessError as exc:
            return respuesta_error_servicio(exc)


