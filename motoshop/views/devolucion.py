# motoshop/views/devolucion.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum

from motoshop.models import Devolucion
from motoshop.serializers.devolucion import DevolucionSerializer, DevolucionCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import DevolucionFilter
from motoshop.permissions import filter_queryset_by_venta_owner
from motoshop.services import BusinessError, DevolucionService
from motoshop.utils.api import respuesta_error_servicio


class DevolucionViewSet(viewsets.ModelViewSet):
    """Devoluciones conectadas a DevolucionService."""
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = DevolucionFilter
    search_fields      = ['motivo']
    ordering_fields    = ['id_devolucion', 'monto_devolucion', 'fecha_solicitud']
    ordering           = ['-fecha_solicitud']
    http_method_names  = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        qs = Devolucion.objects.select_related(
            'id_venta', 'id_venta__id_usuario_cliente',
        ).all()
        return filter_queryset_by_venta_owner(qs, self.request.user)

    def get_permissions(self):
        if self.action in ('aprobar', 'rechazar', 'stats'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return DevolucionCreateSerializer
        return DevolucionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            devolucion = DevolucionService.solicitar(
                data['id_venta'],
                request.user,
                data['motivo'],
                data['monto_devolucion'],
            )
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(DevolucionSerializer(devolucion).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='aprobar')
    def aprobar(self, request, pk=None):
        devolucion = self.get_object()
        try:
            devolucion = DevolucionService.cambiar_estado(devolucion, 'aprobada', request.user)
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(DevolucionSerializer(devolucion).data)

    @action(detail=True, methods=['post'], url_path='rechazar')
    def rechazar(self, request, pk=None):
        devolucion = self.get_object()
        try:
            devolucion = DevolucionService.cambiar_estado(devolucion, 'rechazada', request.user)
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(DevolucionSerializer(devolucion).data)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = Devolucion.objects.all()
        totales = qs.aggregate(
            total_devoluciones=Count('id_devolucion'),
            monto_total=Sum('monto_devolucion'),
        )
        por_estado = {e: qs.filter(estado=e).count() for e, _ in Devolucion.ESTADO_CHOICES}
        return Response({
            'total_devoluciones': totales['total_devoluciones'],
            'monto_total': float(totales['monto_total'] or 0),
            'por_estado': por_estado,
        })
