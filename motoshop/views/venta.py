# motoshop/views/venta.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Venta
from motoshop.serializers.venta import VentaSerializer, VentaCreateSerializer
from motoshop.serializers.financiamiento import (
    FinanciamientoSerializer,
    FinanciamientoCreateSerializer,
)
from motoshop.pagination import StandardPagination
from motoshop.filters    import VentaFilter


class VentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de ventas.
    Las ventas las registra el vendedor/admin a partir de un pedido confirmado.

    Endpoints generados:
      GET    /ventas/                       → listar (propias para clientes, todas para staff)
      POST   /ventas/                       → registrar venta (solo staff)
      GET    /ventas/<id>/                  → detalle
      PATCH  /ventas/<id>/                  → editar estado
      DELETE /ventas/<id>/                  → anular (solo staff)

    Filtros disponibles:
      ?estado=completada
      ?from_date=2025-01-01
      ?to_date=2025-12-31

    Acciones custom:
      POST  /ventas/<id>/financiar/         → agregar financiamiento (solo staff)
      GET   /ventas/stats/                  → estadísticas globales (solo staff)
    """
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
        return VentaSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return (
                Venta.objects
                .select_related('id_pedido', 'id_usuario_cliente', 'id_usuario_vendedor')
                .prefetch_related('financiamientos')
                .all()
            )
        # El cliente solo ve sus propias ventas
        return (
            Venta.objects
            .filter(id_usuario_cliente=user)
            .select_related('id_pedido')
            .prefetch_related('financiamientos')
        )

    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            return [IsAdminUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        pedido = serializer.validated_data['id_pedido']
        serializer.save(
            id_usuario_cliente  = pedido.id_usuario_cliente,
            id_usuario_vendedor = self.request.user,
        )

    # ------------------------------------------------------------------ #
    #  Action: agregar financiamiento                                       #
    # ------------------------------------------------------------------ #
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAdminUser],
        url_path='financiar',
    )
    def financiar(self, request, pk=None):
        """
        Registra un financiamiento para esta venta. Solo staff.
        Body: { "entidad_financiera": "Banco Pichincha", "monto_financiado": 12000, ... }
        """
        venta      = self.get_object()
        serializer = FinanciamientoCreateSerializer(
            data={**request.data, 'id_venta': venta.pk}
        )
        serializer.is_valid(raise_exception=True)
        financiamiento = serializer.save()
        return Response(
            FinanciamientoSerializer(financiamiento).data,
            status=status.HTTP_201_CREATED,
        )

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
        """Resumen de ventas: total, ingresos y conteo por estado. Solo staff."""
        from django.db.models import Count, Sum
        qs     = Venta.objects.all()
        totals = qs.aggregate(
            total_ventas   = Count('id_venta'),
            total_ingresos = Sum('total_venta'),
        )
        by_estado = {
            e: qs.filter(estado=e).count()
            for e, _ in Venta.ESTADO_CHOICES
        }
        return Response({
            'total_ventas':   totals['total_ventas'],
            'total_ingresos': float(totals['total_ingresos'] or 0),
            'por_estado':     by_estado,
        })
