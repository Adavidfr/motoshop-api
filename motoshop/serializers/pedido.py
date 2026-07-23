# motoshop/serializers/pedido.py
from rest_framework import serializers

from motoshop.models import Pedido, CarritoCompras
from motoshop.serializers.carrito_compras import CarritoComprasSerializer
from motoshop.utils.inventario import validar_stock_carrito


class PedidoSerializer(serializers.ModelSerializer):
    """Serializer de pedidos con nombres exactos del esquema SQL."""
    username_cliente = serializers.CharField(
        source='id_usuario_cliente.username', read_only=True
    )
    carrito          = CarritoComprasSerializer(source='id_carrito', read_only=True)

    class Meta:
        model  = Pedido
        fields = [
            'id_pedido', 'username_cliente', 'id_usuario_cliente',
            'id_carrito', 'carrito',
            'estado', 'total', 'fecha_pedido',
        ]
        read_only_fields = ['id_pedido', 'total', 'fecha_pedido',
                            'username_cliente', 'id_usuario_cliente', 'estado']


class PedidoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear un pedido desde un carrito activo.
    Body: { "id_carrito": 1 }
    """
    id_carrito = serializers.PrimaryKeyRelatedField(
        queryset=CarritoCompras.objects.filter(estado='activo'),
    )

    class Meta:
        model  = Pedido
        fields = ['id_carrito']

    def validate_id_carrito(self, carrito):
        request = self.context.get('request')
        if request and carrito.id_usuario_cliente_id != request.user.id:
            raise serializers.ValidationError(
                'El carrito no pertenece al usuario autenticado.'
            )
        if not carrito.items.exists():
            raise serializers.ValidationError(
                'No se puede crear un pedido desde un carrito vacío.'
            )
        validar_stock_carrito(carrito)
        return carrito
