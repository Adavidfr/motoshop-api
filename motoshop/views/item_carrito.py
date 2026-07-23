# motoshop/views/item_carrito.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import ItemCarrito
from motoshop.serializers.item_carrito import ItemCarritoSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters    import ItemCarritoFilter
from motoshop.permissions import IsClientWriteOrStaffReadOnly


class ItemsCarritoViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de items_carrito (tabla: items_carrito).

    Clientes: CRUD sobre ítems de sus propios carritos.
    Administradores: solo lectura.
    """
    serializer_class   = ItemCarritoSerializer
    permission_classes = [IsAuthenticated, IsClientWriteOrStaffReadOnly]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_class    = ItemCarritoFilter
    ordering_fields    = ['id_item', 'cantidad', 'precio_unitario', 'subtotal']
    ordering           = ['id_item']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        if self.request.user.is_staff:
            return ItemCarrito.objects.select_related('id_carrito__id_usuario_cliente').all()
        return ItemCarrito.objects.filter(
            id_carrito__id_usuario_cliente=self.request.user
        ).select_related('id_carrito')

    def perform_create(self, serializer):
        carrito = serializer.validated_data['id_carrito']
        if carrito.id_usuario_cliente_id != self.request.user.id:
            raise PermissionDenied('No tienes permiso para modificar este carrito.')
        serializer.save()

    def perform_update(self, serializer):
        carrito = serializer.instance.id_carrito
        if carrito.id_usuario_cliente_id != self.request.user.id:
            raise PermissionDenied('No tienes permiso para modificar este carrito.')
        serializer.save()

    def perform_destroy(self, instance):
        carrito = instance.id_carrito
        if carrito.id_usuario_cliente_id != self.request.user.id:
            raise PermissionDenied('No tienes permiso para modificar este carrito.')
        instance.delete()

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
