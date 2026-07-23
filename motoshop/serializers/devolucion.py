# motoshop/serializers/devolucion.py
from rest_framework import serializers
from motoshop.models import Devolucion


class DevolucionSerializer(serializers.ModelSerializer):
    """Serializer de devoluciones con nombres exactos del esquema SQL."""

    class Meta:
        model  = Devolucion
        fields = [
            'id_devolucion', 'id_venta',
            'motivo', 'estado', 'monto_devolucion', 'monto_reembolso_aplicado',
            'stock_reintegrado',
            'fecha_solicitud', 'fecha_resolucion',
        ]
        read_only_fields = [
            'id_devolucion', 'fecha_solicitud', 'monto_reembolso_aplicado',
            'stock_reintegrado',
        ]

    def validate_monto_devolucion(self, value):
        if value < 0:
            raise serializers.ValidationError('El monto de devolución no puede ser negativo.')
        return value


class DevolucionCreateSerializer(serializers.ModelSerializer):
    """
    Solicitud de devolución total (sin líneas de detalle).
    monto_devolucion = reembolso solicitado; use 0 para devolución física sin dinero.
    """

    class Meta:
        model  = Devolucion
        fields = ['id_venta', 'motivo', 'monto_devolucion']

    def validate_id_venta(self, venta):
        request = self.context.get('request')
        if request and not request.user.is_staff:
            if venta.id_usuario_cliente_id != request.user.id:
                raise serializers.ValidationError(
                    'Solo puedes solicitar devoluciones sobre tus propias ventas.'
                )
        return venta

    def validate_monto_devolucion(self, value):
        if value < 0:
            raise serializers.ValidationError('El monto no puede ser negativo.')
        return value
