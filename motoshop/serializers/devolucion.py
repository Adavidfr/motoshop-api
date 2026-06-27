# motoshop/serializers/devolucion.py
from rest_framework import serializers
from motoshop.models import Devolucion


class DevolucionSerializer(serializers.ModelSerializer):
    """Serializer de devoluciones con nombres exactos del esquema SQL."""

    class Meta:
        model  = Devolucion
        fields = [
            'id_devolucion', 'id_venta',
            'motivo', 'estado', 'monto_devolucion',
            'fecha_solicitud', 'fecha_resolucion',
        ]
        read_only_fields = ['id_devolucion', 'fecha_solicitud']

    def validate_monto_devolucion(self, value):
        if value <= 0:
            raise serializers.ValidationError('El monto de devolución debe ser mayor a 0.')
        return value


class DevolucionCreateSerializer(serializers.ModelSerializer):
    """Serializer para registrar una solicitud de devolución."""

    class Meta:
        model  = Devolucion
        fields = ['id_venta', 'motivo', 'monto_devolucion']
