# motoshop/serializers/item_carrito.py
from rest_framework import serializers

from motoshop.models import ItemCarrito
from motoshop.utils.inventario import resolver_producto, validar_stock_solicitado


class ItemCarritoSerializer(serializers.ModelSerializer):
    """Serializer de items_carrito con nombres exactos del esquema SQL."""

    class Meta:
        model  = ItemCarrito
        fields = [
            'id_item', 'id_carrito',
            'id_moto', 'id_repuesto',
            'cantidad', 'precio_unitario', 'subtotal',
        ]
        read_only_fields = ['id_item', 'subtotal', 'precio_unitario']

    def validate(self, data):
        if 'precio_unitario' in self.initial_data:
            raise serializers.ValidationError(
                {'precio_unitario': 'El precio se obtiene automáticamente del producto.'}
            )

        id_moto     = data.get('id_moto')
        id_repuesto = data.get('id_repuesto')
        if self.partial:
            id_moto     = id_moto if id_moto is not None else getattr(self.instance, 'id_moto', None)
            id_repuesto = id_repuesto if id_repuesto is not None else getattr(self.instance, 'id_repuesto', None)

        if not id_moto and not id_repuesto:
            if self.partial:
                return data
            raise serializers.ValidationError(
                'Debe especificar id_moto o id_repuesto.'
            )
        if id_moto and id_repuesto:
            raise serializers.ValidationError(
                'Solo puede especificar id_moto O id_repuesto, no ambos.'
            )

        precio, _, _ = resolver_producto(id_moto, id_repuesto)
        data['precio_unitario'] = precio

        cantidad = data.get('cantidad')
        if cantidad is not None:
            carrito = data.get('id_carrito') or getattr(self.instance, 'id_carrito', None)
            exclude_item_id = getattr(self.instance, 'id_item', None)
            validar_stock_solicitado(
                id_moto,
                id_repuesto,
                cantidad,
                carrito=carrito,
                exclude_item_id=exclude_item_id,
            )

        return data

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError('La cantidad debe ser mayor a 0.')
        return value


class AddItemCarritoSerializer(serializers.Serializer):
    """Serializer para la acción add-item del CarritoViewSet."""
    id_moto     = serializers.IntegerField(required=False, allow_null=True)
    id_repuesto = serializers.IntegerField(required=False, allow_null=True)
    cantidad    = serializers.IntegerField(min_value=1)

    def validate(self, data):
        if 'precio_unitario' in self.initial_data:
            raise serializers.ValidationError(
                {'precio_unitario': 'El precio se obtiene automáticamente del producto.'}
            )

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

        precio, _, _ = resolver_producto(id_moto, id_repuesto)
        data['precio_unitario'] = precio

        carrito = self.context.get('carrito')
        item_existente = self.context.get('item_existente')
        cantidad_final = data['cantidad']
        if item_existente:
            cantidad_final += item_existente.cantidad

        validar_stock_solicitado(
            id_moto,
            id_repuesto,
            cantidad_final,
            carrito=carrito,
            exclude_item_id=getattr(item_existente, 'id_item', None),
        )
        return data
