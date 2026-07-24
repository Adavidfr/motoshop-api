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
        read_only_fields = ['id_seguro', 'numero_poliza']

    def validate(self, attrs):
        fecha_inicio = attrs.get('fecha_inicio', getattr(self.instance, 'fecha_inicio', None))
        fecha_fin    = attrs.get('fecha_fin', getattr(self.instance, 'fecha_fin', None))
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise serializers.ValidationError(
                {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'}
            )
        return attrs

    def validate_costo_anual(self, value):
        if value < 0:
            raise serializers.ValidationError('El costo anual no puede ser negativo.')
        return value


class SeguroCreateSerializer(serializers.ModelSerializer):
    """
    Registro de seguro. numero_poliza lo genera el servidor (read_only / ignorado).
    Payload: id_venta, aseguradora, tipo_cobertura, fechas, costo_anual [, estado].
    """

    class Meta:
        model  = Seguro
        fields = [
            'id_venta', 'aseguradora', 'numero_poliza', 'tipo_cobertura',
            'fecha_inicio', 'fecha_fin', 'costo_anual', 'estado',
        ]
        read_only_fields = ['numero_poliza']

    def validate(self, attrs):
        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin    = attrs.get('fecha_fin')
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise serializers.ValidationError(
                {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'}
            )
        return attrs

    def validate_costo_anual(self, value):
        if value < 0:
            raise serializers.ValidationError('El costo anual no puede ser negativo.')
        return value
