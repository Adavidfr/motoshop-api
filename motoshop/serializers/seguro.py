# motoshop/serializers/seguro.py
from rest_framework import serializers
from motoshop.models import Seguro


class SeguroSerializer(serializers.ModelSerializer):
    """Serializer de seguros con nombres exactos del esquema SQL."""

    class Meta:
        model  = Seguro
        fields = [
            'id_seguro', 'id_venta',
            'aseguradora', 'numero_poliza', 'tipo_cobertura',
            'fecha_inicio', 'fecha_fin', 'costo_anual', 'estado',
        ]
        read_only_fields = ['id_seguro']

    def validate(self, attrs):
        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin    = attrs.get('fecha_fin')
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise serializers.ValidationError(
                {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'}
            )
        return attrs

    def validate_costo_anual(self, value):
        if value <= 0:
            raise serializers.ValidationError('El costo anual debe ser mayor a 0.')
        return value


class SeguroCreateSerializer(serializers.ModelSerializer):
    """Serializer para registrar un seguro."""

    class Meta:
        model  = Seguro
        fields = [
            'id_venta', 'aseguradora', 'numero_poliza', 'tipo_cobertura',
            'fecha_inicio', 'fecha_fin', 'costo_anual', 'estado',
        ]
