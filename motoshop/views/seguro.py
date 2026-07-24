# motoshop/views/seguro.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Seguro
from motoshop.serializers.seguro import SeguroSerializer, SeguroCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import SeguroFilter
from motoshop.permissions import filter_queryset_by_venta_owner
from motoshop.services import BusinessError, SeguroService
from motoshop.utils.api import respuesta_error_servicio


class SeguroViewSet(viewsets.ModelViewSet):
    """
    Seguros: lectura filtrada para clientes, gestión completa para administradores.
    numero_poliza se genera en create; no es editable.
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            seguro = SeguroService.crear(
                venta=data['id_venta'],
                aseguradora=data['aseguradora'],
                tipo_cobertura=data['tipo_cobertura'],
                fecha_inicio=data['fecha_inicio'],
                fecha_fin=data['fecha_fin'],
                costo_anual=data['costo_anual'],
                estado=data.get('estado', 'activo'),
            )
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(SeguroSerializer(seguro).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        # numero_poliza es read_only en el serializer; no se acepta cambio manual.
        return super().partial_update(request, *args, **kwargs)
