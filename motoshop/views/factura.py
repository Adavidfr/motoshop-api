# motoshop/views/factura.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Factura
from motoshop.serializers.factura import FacturaSerializer, FacturaCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import FacturaFilter
from motoshop.permissions import filter_queryset_by_venta_owner
from motoshop.services import BusinessError, FacturaService
from motoshop.utils.api import respuesta_error_servicio


class FacturaViewSet(viewsets.ModelViewSet):
    """Facturas conectadas a FacturaService."""
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = FacturaFilter
    search_fields      = ['numero_factura']
    ordering_fields    = ['id_factura', 'fecha_emision', 'total']
    ordering           = ['-fecha_emision']
    http_method_names  = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        qs = Factura.objects.select_related(
            'id_venta', 'id_venta__id_usuario_cliente',
        ).all()
        return filter_queryset_by_venta_owner(qs, self.request.user)

    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return FacturaCreateSerializer
        return FacturaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            factura = FacturaService.emitir(data['id_venta'], procesado_por=request.user)
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(FacturaSerializer(factura).data, status=201)

