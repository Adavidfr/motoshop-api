# motoshop/views/venta.py
from django.db.models.deletion import ProtectedError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Venta
from motoshop.serializers.venta import (
    VentaSerializer,
    VentaCreateSerializer,
    VentaDetailSerializer,
)
from motoshop.serializers.financiamiento import (
    FinanciamientoSerializer,
    FinanciamientoCreateSerializer,
)
from motoshop.pagination import StandardPagination
from motoshop.filters import VentaFilter
from motoshop.services import BusinessError, FinanciamientoService, VentaService
from motoshop.utils.api import respuesta_error_servicio


class VentaViewSet(viewsets.ModelViewSet):
    """ViewSet CRUD de ventas conectado a VentaService."""
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_class    = VentaFilter
    ordering_fields    = ['fecha_venta', 'total_venta']
    ordering           = ['-fecha_venta']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return VentaCreateSerializer
        if self.action == 'retrieve':
            return VentaDetailSerializer
        return VentaSerializer

    def get_queryset(self):
        user = self.request.user
        base = (
            Venta.objects
            .select_related('id_pedido', 'id_usuario_cliente', 'id_usuario_vendedor')
            .prefetch_related('financiamientos', 'pagos', 'garantias', 'seguros', 'documentos')
        )
        if user.is_staff:
            return base.all()
        return base.filter(id_usuario_cliente=user)

    def get_permissions(self):
        if self.action in ('create', 'destroy', 'update', 'partial_update', 'financiar'):
            return [IsAdminUser()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.validated_data['id_pedido']
        estado = serializer.validated_data.get('estado', 'pendiente')
        try:
            venta = VentaService.crear_venta_desde_pedido(
                pedido.pk,
                request.user,
                estado=estado,
            )
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(
            VentaDetailSerializer(venta).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        venta = self.get_object()
        nuevo_estado = request.data.get('estado')
        if nuevo_estado and nuevo_estado != venta.estado:
            observacion = request.data.get('observacion', '')
            try:
                venta = VentaService.cambiar_estado(
                    venta, nuevo_estado, request.user, observacion,
                )
            except BusinessError as exc:
                return respuesta_error_servicio(exc)
            return Response(VentaDetailSerializer(venta).data)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError as e:
            modelos_relacionados = ', '.join(
                str(obj) for obj in list(e.protected_objects)[:5]
            )
            return Response(
                {
                    'error': 'No se puede eliminar la venta porque tiene registros relacionados.',
                    'detalle': f'Registros asociados: {modelos_relacionados}',
                },
                status=status.HTTP_409_CONFLICT,
            )

    @action(detail=True, methods=['get'], url_path='resumen')
    def resumen(self, request, pk=None):
        venta = self.get_object()
        return Response(VentaService.construir_resumen(venta))

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAdminUser],
        url_path='financiar',
    )
    def financiar(self, request, pk=None):
        venta = self.get_object()
        serializer = FinanciamientoCreateSerializer(data={**request.data, 'id_venta': venta.pk})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            financiamiento = FinanciamientoService.crear(
                venta=venta,
                entidad_financiera=data['entidad_financiera'],
                monto_financiado=data['monto_financiado'],
                tasa_interes=data['tasa_interes'],
                plazo_meses=data['plazo_meses'],
                entrada=data.get('entrada', 0),
                estado=data.get('estado', 'activo'),
            )
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(
            FinanciamientoSerializer(financiamiento).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAdminUser],
        url_path='stats',
    )
    def stats(self, request):
        from django.db.models import Count, Sum
        qs = Venta.objects.all()
        totals = qs.aggregate(
            total_ventas=Count('id_venta'),
            total_ingresos=Sum('total_venta'),
        )
        by_estado = {e: qs.filter(estado=e).count() for e, _ in Venta.ESTADO_CHOICES}
        return Response({
            'total_ventas': totals['total_ventas'],
            'total_ingresos': float(totals['total_ingresos'] or 0),
            'por_estado': by_estado,
        })
