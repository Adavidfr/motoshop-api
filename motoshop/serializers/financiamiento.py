# motoshop/serializers/financiamiento.py
from rest_framework import serializers
from motoshop.models import Financiamiento


class FinanciamientoSerializer(serializers.ModelSerializer):
    """Serializer de financiamientos con nombres exactos del esquema SQL."""

    class Meta:
        model  = Financiamiento
        fields = [
            'id_financiamiento', 'id_venta',
            'entidad_financiera', 'monto_financiado',
            'tasa_interes', 'plazo_meses', 'cuota_mensual', 'estado',
        ]
        read_only_fields = ['id_financiamiento']

    def validate_monto_financiado(self, value):
        if value <= 0:
            raise serializers.ValidationError('El monto financiado debe ser mayor a 0.')
        return value

    def validate_tasa_interes(self, value):
        if value <= 0 or value > 100:
            raise serializers.ValidationError('La tasa de interés debe estar entre 0 y 100.')
        return value

    def validate_plazo_meses(self, value):
        if value <= 0:
            raise serializers.ValidationError('El plazo en meses debe ser mayor a 0.')
        return value

    def validate_cuota_mensual(self, value):
        if value <= 0:
            raise serializers.ValidationError('La cuota mensual debe ser mayor a 0.')
        return value


class FinanciamientoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear un financiamiento. id_venta se provee en el body."""

    class Meta:
        model  = Financiamiento
        fields = [
            'id_venta', 'entidad_financiera', 'monto_financiado',
            'tasa_interes', 'plazo_meses', 'cuota_mensual', 'estado',
        ]
