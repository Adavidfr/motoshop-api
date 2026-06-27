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
from motoshop.filters    import PedidoFilter


class PedidoViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de pedidos.

    Endpoints:
      GET    /pedidos/                      → listar (propios / todos para staff)
      POST   /pedidos/                      → crear pedido desde un id_carrito activo
      GET    /pedidos/<id_pedido>/          → detalle
      PATCH  /pedidos/<id_pedido>/          → editar (solo staff)
      DELETE /pedidos/<id_pedido>/          → eliminar (solo staff)

    Filtros: ?estado=pending  ?from_date=2025-01-01  ?to_date=2025-12-31

    Acciones custom:
      POST  /pedidos/<id_pedido>/confirm/         → confirmar (pending → confirmed)
      POST  /pedidos/<id_pedido>/update-status/   → cambiar estado (solo staff)
      GET   /pedidos/stats/                       → estadísticas (solo staff)
    """
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

    def perform_create(self, serializer):
        carrito = serializer.validated_data['id_carrito']
        total   = carrito.calcular_total()
        serializer.save(
            id_usuario_cliente = self.request.user,
            total              = total,
        )
        # Marcar el carrito como procesado
        carrito.estado = 'procesado'
        carrito.save(update_fields=['estado'])

    # ------------------------------------------------------------------ #
    #  Action: confirmar pedido                                            #
    # ------------------------------------------------------------------ #
    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """Confirma un pedido en estado 'pending' que tenga ítems."""
        pedido = self.get_object()
        if pedido.estado != 'pending':
            return Response(
                {'error': 'Solo se pueden confirmar pedidos en estado "pending".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if pedido.id_carrito and not pedido.id_carrito.items.exists():
            return Response(
                {'error': 'No se puede confirmar un pedido con el carrito vacío.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pedido.estado = 'confirmed'
        pedido.save(update_fields=['estado'])
        return Response(PedidoSerializer(pedido).data)

    # ------------------------------------------------------------------ #
    #  Action: actualizar estado (solo staff)                              #
    # ------------------------------------------------------------------ #
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAdminUser],
        url_path='update-status',
    )
    def update_status(self, request, pk=None):
        """Cambia el estado del pedido a cualquier valor válido. Solo staff."""
        pedido         = self.get_object()
        nuevo_estado   = request.data.get('estado')
        estados_validos = [s[0] for s in Pedido.ESTADO_CHOICES]

        if nuevo_estado not in estados_validos:
            return Response(
                {'error': f'Estado inválido. Opciones: {estados_validos}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pedido.estado = nuevo_estado
        pedido.save(update_fields=['estado'])
        return Response(PedidoSerializer(pedido).data)

    # ------------------------------------------------------------------ #
    #  Action: estadísticas (solo staff)                                   #
    # ------------------------------------------------------------------ #
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAdminUser],
        url_path='stats',
    )
    def stats(self, request):
        """Resumen de pedidos: total, ingresos y conteo por estado."""
        from django.db.models import Count, Sum
        qs     = Pedido.objects.all()
        totals = qs.aggregate(
            total_pedidos  = Count('id_pedido'),
            total_ingresos = Sum('total'),
        )
        por_estado = {
            s: qs.filter(estado=s).count()
            for s, _ in Pedido.ESTADO_CHOICES
        }
        return Response({
            'total_pedidos':  totals['total_pedidos'],
            'total_ingresos': float(totals['total_ingresos'] or 0),
            'por_estado':     por_estado,
        })
