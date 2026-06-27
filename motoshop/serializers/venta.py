# motoshop/serializers/venta.py
from rest_framework import serializers
from motoshop.models import Venta, Pedido
from motoshop.serializers.financiamiento import FinanciamientoSerializer


class VentaSerializer(serializers.ModelSerializer):
    """Serializer de ventas con nombres exactos del esquema SQL."""
    financiamientos     = FinanciamientoSerializer(many=True, read_only=True)
    username_cliente    = serializers.CharField(
        source='id_usuario_cliente.username', read_only=True
    )
    username_vendedor   = serializers.CharField(
        source='id_usuario_vendedor.username', read_only=True
    )
    num_financiamientos = serializers.SerializerMethodField()

    class Meta:
        model  = Venta
        fields = [
            'id_venta', 'id_pedido',
            'username_cliente',  'id_usuario_cliente',
            'username_vendedor', 'id_usuario_vendedor',
            'total_venta', 'estado', 'fecha_venta',
            'num_financiamientos', 'financiamientos',
        ]
        read_only_fields = [
            'id_venta', 'fecha_venta',
            'username_cliente',  'id_usuario_cliente',
            'username_vendedor', 'id_usuario_vendedor',
        ]

    def get_num_financiamientos(self, obj):
        return obj.financiamientos.count()

    def validate_total_venta(self, value):
        if value <= 0:
            raise serializers.ValidationError('El total de la venta debe ser mayor a 0.')
        return value


class VentaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para registrar una venta desde un pedido confirmado.
    Body: { "id_pedido": 1, "total_venta": "15000.00", "estado": "completada" }
    """
    id_pedido = serializers.PrimaryKeyRelatedField(
        queryset=Pedido.objects.filter(estado='confirmed'),
    )

    class Meta:
        model  = Venta
        fields = ['id_pedido', 'total_venta', 'estado']
