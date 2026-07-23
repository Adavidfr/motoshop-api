from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Mantenimiento
from motoshop.serializers.mantenimiento import MantenimientoSerializer
from motoshop.filters import MantenimientoFilter
from motoshop.pagination import StandardPagination
from motoshop.services import BusinessError, MantenimientoService
from motoshop.utils.api import respuesta_error_servicio


class MantenimientoViewSet(viewsets.ModelViewSet):
    """Mantenimientos conectados a MantenimientoService."""
    serializer_class = MantenimientoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MantenimientoFilter
    search_fields = [
        'moto__modelo', 'usuario_cliente__username', 'usuario_cliente__email',
        'servicio__nombre', 'diagnostico_inicial', 'estado',
    ]
    ordering_fields = ['fecha_registro', 'kilometraje_actual', 'costo_final', 'estado']
    ordering = ['-fecha_registro']

    def get_queryset(self):
        qs = Mantenimiento.objects.select_related('moto', 'usuario_cliente', 'servicio').all()
        if not self.request.user.is_staff:
            qs = qs.filter(usuario_cliente=self.request.user)
        return qs

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy', 'stats', 'finalizar', 'update_status'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()
        else:
            serializer.save(usuario_cliente=self.request.user)

    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar(self, request, pk=None):
        mantenimiento = self.get_object()
        try:
            mantenimiento = MantenimientoService.cambiar_estado(
                mantenimiento, 'Finalizado', request.user,
            )
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(MantenimientoSerializer(mantenimiento).data)

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        mantenimiento = self.get_object()
        nuevo_estado = request.data.get('estado')
        try:
            mantenimiento = MantenimientoService.cambiar_estado(
                mantenimiento, nuevo_estado, request.user,
            )
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(MantenimientoSerializer(mantenimiento).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser], url_path='stats')
    def stats(self, request):
        qs = Mantenimiento.objects.all()
        return Response({
            'total': qs.count(),
            'pendientes': qs.filter(estado__iexact='Pendiente').count(),
            'en_proceso': qs.filter(estado__iexact='En proceso').count(),
            'finalizados': qs.filter(estado__iexact='Finalizado').count(),
            'cancelados': qs.filter(estado__iexact='Cancelado').count(),
        })
