# motoshop/serializers/financiamiento.py
from rest_framework import serializers
from motoshop.models import Financiamiento


class FinanciamientoSerializer(serializers.ModelSerializer):
    """Serializer de financiamientos con nombres exactos del esquema SQL."""

    class Meta:
        model  = Financiamiento
        fields = [
            'id_financiamiento', 'id_venta',
            'entidad_financiera', 'monto_financiado', 'entrada', 'saldo_pendiente',
            'tasa_interes', 'plazo_meses', 'cuota_mensual', 'estado',
        ]
        read_only_fields = ['id_financiamiento', 'cuota_mensual', 'saldo_pendiente']


class FinanciamientoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear un financiamiento (validación de formato)."""

    class Meta:
        model  = Financiamiento
        fields = [
            'id_venta', 'entidad_financiera', 'monto_financiado', 'entrada',
            'tasa_interes', 'plazo_meses', 'estado',
        ]

    def validate_monto_financiado(self, value):
        if value <= 0:
            raise serializers.ValidationError('El monto financiado debe ser mayor a 0.')
        return value

    def validate_plazo_meses(self, value):
        if value <= 0:
            raise serializers.ValidationError('El plazo en meses debe ser mayor a 0.')
        return value
