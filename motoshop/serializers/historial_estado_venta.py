# motoshop/serializers/historial_estado_venta.py
from rest_framework import serializers
from motoshop.models import HistorialEstadoVenta


class HistorialEstadoVentaSerializer(serializers.ModelSerializer):
    """Serializer del historial de estados de venta con nombres exactos del esquema SQL."""

    class Meta:
        model  = HistorialEstadoVenta
        fields = [
            'id_historial', 'id_venta',
            'estado_anterior', 'estado_nuevo',
            'fecha_cambio', 'observacion',
        ]
        read_only_fields = ['id_historial', 'fecha_cambio']


class HistorialEstadoVentaCreateSerializer(serializers.ModelSerializer):
    """Serializer para registrar un cambio de estado en una venta."""

    class Meta:
        model  = HistorialEstadoVenta
        fields = ['id_venta', 'estado_anterior', 'estado_nuevo', 'observacion']
