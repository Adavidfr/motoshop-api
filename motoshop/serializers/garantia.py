# motoshop/serializers/garantia.py
from rest_framework import serializers
from motoshop.models import Garantia


class GarantiaSerializer(serializers.ModelSerializer):
    """Serializer de garantías con nombres exactos del esquema SQL."""

    class Meta:
        model  = Garantia
        fields = [
            'id_garantia', 'id_venta', 'id_moto',
            'meses_garantia', 'fecha_inicio', 'fecha_fin',
            'descripcion', 'estado',
        ]
        read_only_fields = ['id_garantia']

    def validate(self, attrs):
        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin    = attrs.get('fecha_fin')
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise serializers.ValidationError(
                {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'}
            )
        return attrs

    def validate_meses_garantia(self, value):
        if value <= 0:
            raise serializers.ValidationError('Los meses de garantía deben ser mayor a 0.')
        return value


class GarantiaCreateSerializer(serializers.ModelSerializer):
    """Serializer para registrar una garantía."""

    class Meta:
        model  = Garantia
        fields = [
            'id_venta', 'id_moto', 'meses_garantia',
            'fecha_inicio', 'fecha_fin', 'descripcion', 'estado',
        ]
