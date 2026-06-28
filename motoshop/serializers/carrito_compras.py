# motoshop/serializers/carrito_compras.py
from rest_framework import serializers
from motoshop.models import CarritoCompras
from motoshop.serializers.item_carrito import ItemCarritoSerializer


class CarritoComprasSerializer(serializers.ModelSerializer):
    """Serializer de carrito_compras con nombres exactos del esquema SQL."""
    items             = ItemCarritoSerializer(many=True, read_only=True)
    username_cliente  = serializers.CharField(
        source='id_usuario_cliente.username', read_only=True
    )
    num_items         = serializers.SerializerMethodField()
    total             = serializers.SerializerMethodField()

    class Meta:
        model  = CarritoCompras
        fields = [
            'id_carrito', 'username_cliente', 'id_usuario_cliente',
            'estado', 'fecha_creacion',
            'num_items', 'total', 'items',
        ]
        read_only_fields = ['id_carrito', 'username_cliente', 'id_usuario_cliente', 'fecha_creacion']

    def get_num_items(self, obj):
        return obj.items.count()

    def get_total(self, obj):
        return float(obj.calcular_total())

    def validate_estado(self, value):
        opciones = [e[0] for e in CarritoCompras.ESTADO_CHOICES]
        if value not in opciones:
            raise serializers.ValidationError(
                f'Estado inválido. Opciones: {opciones}'
            )
        return value
