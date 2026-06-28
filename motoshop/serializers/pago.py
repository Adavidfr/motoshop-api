# motoshop/serializers/pago.py
from rest_framework import serializers
from motoshop.models import Pago


class PagoSerializer(serializers.ModelSerializer):
    """Serializer de pagos con nombres exactos del esquema SQL."""

    class Meta:
        model  = Pago
        fields = [
            'id_pago', 'id_venta',
            'monto', 'metodo_pago', 'estado',
            'fecha_pago', 'referencia',
        ]
        read_only_fields = ['id_pago', 'fecha_pago']

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError('El monto del pago debe ser mayor a 0.')
        return value


class PagoCreateSerializer(serializers.ModelSerializer):
    """Serializer para registrar un nuevo pago."""

    class Meta:
        model  = Pago
        fields = ['id_venta', 'monto', 'metodo_pago', 'estado', 'referencia']
