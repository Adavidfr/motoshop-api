# motoshop/views/garantia.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Garantia
from motoshop.serializers.garantia import GarantiaSerializer, GarantiaCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import GarantiaFilter
from motoshop.permissions import filter_queryset_by_venta_owner
from motoshop.services import BusinessError, GarantiaService
from motoshop.utils.api import respuesta_error_servicio


class GarantiaViewSet(viewsets.ModelViewSet):
    """Garantías conectadas a GarantiaService."""
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = GarantiaFilter
    search_fields      = ['descripcion']
    ordering_fields    = ['id_garantia', 'fecha_inicio', 'fecha_fin', 'meses_garantia']
    ordering           = ['-fecha_inicio']
    http_method_names  = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = Garantia.objects.select_related(
            'id_venta', 'id_venta__id_usuario_cliente', 'id_moto',
        ).all()
        return filter_queryset_by_venta_owner(qs, self.request.user)

    def get_permissions(self):
        if self.action in ('create', 'partial_update', 'update'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return GarantiaCreateSerializer
        return GarantiaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        moto = data['id_moto']
        try:
            garantia = GarantiaService.crear(
                venta=data['id_venta'],
                moto_id=moto.pk if hasattr(moto, 'pk') else moto,
                meses_garantia=data['meses_garantia'],
                fecha_inicio=data['fecha_inicio'],
                fecha_fin=data['fecha_fin'],
                descripcion=data.get('descripcion', ''),
                estado=data.get('estado', 'activa'),
            )
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(GarantiaSerializer(garantia).data, status=201)

    def partial_update(self, request, *args, **kwargs):
        garantia = self.get_object()
        nuevo_estado = request.data.get('estado')
        if nuevo_estado and nuevo_estado != garantia.estado:
            try:
                garantia = GarantiaService.cambiar_estado(garantia, nuevo_estado)
            except BusinessError as exc:
                return respuesta_error_servicio(exc)
            return Response(GarantiaSerializer(garantia).data)
        return super().partial_update(request, *args, **kwargs)
