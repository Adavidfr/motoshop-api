# motoshop/views/carrito_compras.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import CarritoCompras, ItemCarrito
from motoshop.serializers.carrito_compras import CarritoComprasSerializer
from motoshop.serializers.item_carrito    import AddItemCarritoSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters    import CarritoFilter


class CarritoComprasViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de carrito_compras (tabla: carrito_compras).

    Endpoints:
      GET    /carritos/                     → listar (propios / todos para staff)
      POST   /carritos/                     → crear carrito nuevo
      GET    /carritos/<id_carrito>/        → detalle
      PATCH  /carritos/<id_carrito>/        → editar estado
      DELETE /carritos/<id_carrito>/        → eliminar

    Acciones custom:
      GET    /carritos/activo/                           → carrito activo del usuario
      POST   /carritos/<id_carrito>/add-item/            → agregar ítem
      DELETE /carritos/<id_carrito>/remove-item/<id>/    → quitar ítem
      POST   /carritos/<id_carrito>/vaciar/              → eliminar todos los ítems
    """
    serializer_class   = CarritoComprasSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_class    = CarritoFilter
    ordering_fields    = ['fecha_creacion']
    ordering           = ['-fecha_creacion']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        if self.request.user.is_staff:
            return (
                CarritoCompras.objects
                .select_related('id_usuario_cliente')
                .prefetch_related('items')
                .all()
            )
        return (
            CarritoCompras.objects
            .filter(id_usuario_cliente=self.request.user)
            .prefetch_related('items')
        )

    def perform_create(self, serializer):
        serializer.save(id_usuario_cliente=self.request.user)

    # ------------------------------------------------------------------ #
    #  Action: carrito activo                                              #
    # ------------------------------------------------------------------ #
    @action(detail=False, methods=['get'], url_path='activo')
    def activo(self, request):
        """Devuelve el carrito activo del usuario autenticado."""
        carrito = (
            CarritoCompras.objects
            .filter(id_usuario_cliente=request.user, estado='activo')
            .prefetch_related('items')
            .first()
        )
        if not carrito:
            return Response(
                {'detail': 'No tienes un carrito activo.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(CarritoComprasSerializer(carrito).data)

    # ------------------------------------------------------------------ #
    #  Action: agregar ítem                                                #
    # ------------------------------------------------------------------ #
    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        """
        Agrega un ítem al carrito (solo si está activo).
        Body: { "id_moto": 1, "cantidad": 2, "precio_unitario": "15000.00" }
              { "id_repuesto": 5, "cantidad": 1, "precio_unitario": "250.00" }
        """
        carrito = self.get_object()
        if carrito.estado != 'activo':
            return Response(
                {'error': f'No se puede modificar un carrito con estado "{carrito.estado}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AddItemCarritoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        id_moto     = data.get('id_moto')
        id_repuesto = data.get('id_repuesto')

        filtro = {'id_carrito': carrito}
        if id_moto:
            filtro['id_moto'] = id_moto
        else:
            filtro['id_repuesto'] = id_repuesto

        item_existente = ItemCarrito.objects.filter(**filtro).first()

        if item_existente:
            item_existente.cantidad       += data['cantidad']
            item_existente.precio_unitario = data['precio_unitario']
            item_existente.save()
        else:
            ItemCarrito.objects.create(
                id_carrito      = carrito,
                id_moto         = id_moto,
                id_repuesto     = id_repuesto,
                cantidad        = data['cantidad'],
                precio_unitario = data['precio_unitario'],
            )

        return Response(CarritoComprasSerializer(carrito).data)

    # ------------------------------------------------------------------ #
    #  Action: quitar ítem                                                 #
    # ------------------------------------------------------------------ #
    @action(detail=True, methods=['delete'], url_path=r'remove-item/(?P<item_id>[^/.]+)')
    def remove_item(self, request, pk=None, item_id=None):
        """DELETE /carritos/<id_carrito>/remove-item/<id_item>/"""
        carrito = self.get_object()
        try:
            item = ItemCarrito.objects.get(id_item=item_id, id_carrito=carrito)
        except ItemCarrito.DoesNotExist:
            return Response(
                {'error': 'Ítem no encontrado en este carrito.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        item.delete()
        return Response(CarritoComprasSerializer(carrito).data)

    # ------------------------------------------------------------------ #
    #  Action: vaciar carrito                                              #
    # ------------------------------------------------------------------ #
    @action(detail=True, methods=['post'], url_path='vaciar')
    def vaciar(self, request, pk=None):
        """Elimina todos los ítems del carrito."""
        carrito = self.get_object()
        if carrito.estado != 'activo':
            return Response(
                {'error': f'No se puede vaciar un carrito con estado "{carrito.estado}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        carrito.items.all().delete()
        return Response(CarritoComprasSerializer(carrito).data)
