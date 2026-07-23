# motoshop/views/pedido.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Pedido
from motoshop.serializers.pedido import PedidoSerializer, PedidoCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import PedidoFilter
from motoshop.services import BusinessError, PedidoService
from motoshop.utils.api import respuesta_error_servicio


class PedidoViewSet(viewsets.ModelViewSet):
    """ViewSet CRUD de pedidos conectado a PedidoService."""
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_class    = PedidoFilter
    ordering_fields    = ['fecha_pedido', 'total']
    ordering           = ['-fecha_pedido']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return PedidoCreateSerializer
        return PedidoSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_permissions(self):
        if self.action == 'create':
            from motoshop.permissions import IsClientWriteOrStaffReadOnly
            return [IsAuthenticated(), IsClientWriteOrStaffReadOnly()]
        if self.action in ('update', 'partial_update', 'destroy', 'update_status'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_staff:
            return (
                Pedido.objects
                .select_related('id_usuario_cliente', 'id_carrito')
                .prefetch_related('id_carrito__items')
                .all()
            )
        return (
            Pedido.objects
            .filter(id_usuario_cliente=self.request.user)
            .select_related('id_carrito')
            .prefetch_related('id_carrito__items')
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            pedido = PedidoService.crear_desde_carrito(
                request.user,
                serializer.validated_data['id_carrito'],
            )
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(
            PedidoSerializer(pedido).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        pedido = self.get_object()
        try:
            pedido = PedidoService.confirmar(pedido, request.user)
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(PedidoSerializer(pedido).data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAdminUser],
        url_path='update-status',
    )
    def update_status(self, request, pk=None):
        pedido = self.get_object()
        nuevo_estado = request.data.get('estado')
        try:
            pedido = PedidoService.cambiar_estado(pedido, nuevo_estado, request.user)
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(PedidoSerializer(pedido).data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAdminUser],
        url_path='stats',
    )
    def stats(self, request):
        from django.db.models import Count, Sum
        qs = Pedido.objects.all()
        totals = qs.aggregate(
            total_pedidos=Count('id_pedido'),
            total_ingresos=Sum('total'),
        )
        por_estado = {s: qs.filter(estado=s).count() for s, _ in Pedido.ESTADO_CHOICES}
        return Response({
            'total_pedidos': totals['total_pedidos'],
            'total_ingresos': float(totals['total_ingresos'] or 0),
            'por_estado': por_estado,
        })
