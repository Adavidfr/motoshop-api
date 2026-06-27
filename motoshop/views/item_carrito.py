# motoshop/views/item_carrito.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import ItemCarrito
from motoshop.serializers.item_carrito import ItemCarritoSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters    import ItemCarritoFilter


class ItemsCarritoViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de items_carrito (tabla: items_carrito).

    Endpoints:
      GET    /items-carrito/              → listar (filtrar por id_carrito)
      POST   /items-carrito/              → crear ítem directamente
      GET    /items-carrito/<id_item>/    → detalle
      PATCH  /items-carrito/<id_item>/    → editar cantidad / precio_unitario
      DELETE /items-carrito/<id_item>/    → eliminar

    Filtros: ?id_carrito=1  ?id_moto=2  ?id_repuesto=3

    Acción custom:
      GET  /items-carrito/stats/  → estadísticas (solo staff)
    """
    serializer_class   = ItemCarritoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_class    = ItemCarritoFilter
    ordering_fields    = ['id_item', 'cantidad', 'precio_unitario', 'subtotal']
    ordering           = ['id_item']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        if self.request.user.is_staff:
            return ItemCarrito.objects.select_related('id_carrito__id_usuario_cliente').all()
        # El cliente solo ve ítems de sus propios carritos
        return ItemCarrito.objects.filter(
            id_carrito__id_usuario_cliente=self.request.user
        ).select_related('id_carrito')

    # ------------------------------------------------------------------ #
    #  Action: estadísticas (solo staff)                                   #
    # ------------------------------------------------------------------ #
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser], url_path='stats')
    def stats(self, request):
        """Resumen de ítems del carrito. Solo staff."""
        from django.db.models import Count, Sum, Avg
        qs   = ItemCarrito.objects.all()
        data = qs.aggregate(
            total_items     = Count('id_item'),
            total_unidades  = Sum('cantidad'),
            subtotal_total  = Sum('subtotal'),
            precio_promedio = Avg('precio_unitario'),
        )
        return Response({
            'total_items':     data['total_items'],
            'total_unidades':  data['total_unidades'] or 0,
            'subtotal_total':  float(data['subtotal_total'] or 0),
            'precio_promedio': round(float(data['precio_promedio'] or 0), 2),
            'por_tipo': {
                'motos':     qs.filter(id_moto__isnull=False).count(),
                'repuestos': qs.filter(id_repuesto__isnull=False).count(),
            },
        })
