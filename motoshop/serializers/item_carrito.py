# motoshop/serializers/item_carrito.py
from rest_framework import serializers
from motoshop.models import ItemCarrito


class ItemCarritoSerializer(serializers.ModelSerializer):
    """Serializer de items_carrito con nombres exactos del esquema SQL."""

    class Meta:
        model  = ItemCarrito
        fields = [
            'id_item', 'id_carrito',
            'id_moto', 'id_repuesto',
            'cantidad', 'precio_unitario', 'subtotal',
        ]
        read_only_fields = ['id_item', 'subtotal']

    def validate(self, data):
        id_moto     = data.get('id_moto')
        id_repuesto = data.get('id_repuesto')
        if not id_moto and not id_repuesto:
            raise serializers.ValidationError(
                'Debe especificar id_moto o id_repuesto.'
            )
        if id_moto and id_repuesto:
            raise serializers.ValidationError(
                'Solo puede especificar id_moto O id_repuesto, no ambos.'
            )
        return data

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError('La cantidad debe ser mayor a 0.')
        return value

    def validate_precio_unitario(self, value):
        if value <= 0:
            raise serializers.ValidationError('El precio unitario debe ser mayor a 0.')
        return value


class AddItemCarritoSerializer(serializers.Serializer):
    """Serializer para la acción add-item del CarritoViewSet."""
    id_moto         = serializers.IntegerField(required=False, allow_null=True)
    id_repuesto     = serializers.IntegerField(required=False, allow_null=True)
    cantidad        = serializers.IntegerField(min_value=1)
    precio_unitario = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate(self, data):
        id_moto     = data.get('id_moto')
        id_repuesto = data.get('id_repuesto')
        if not id_moto and not id_repuesto:
            raise serializers.ValidationError(
                'Debe especificar id_moto o id_repuesto.'
            )
        if id_moto and id_repuesto:
            raise serializers.ValidationError(
                'Solo puede especificar id_moto O id_repuesto, no ambos.'
            )
        return data
