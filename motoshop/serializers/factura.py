# motoshop/serializers/factura.py
from rest_framework import serializers
from motoshop.models import Factura


class FacturaSerializer(serializers.ModelSerializer):
    """Serializer de facturas con nombres exactos del esquema SQL."""

    id_venta = serializers.IntegerField(source='id_pago.id_venta_id', read_only=True)

    class Meta:
        model  = Factura
        fields = [
            'id_factura', 'id_pago', 'id_venta',
            'numero_factura', 'fecha_emision',
            'subtotal', 'iva', 'total',
        ]
        read_only_fields = [
            'id_factura', 'id_venta', 'fecha_emision',
            'subtotal', 'iva', 'total',
        ]


class FacturaCreateSerializer(serializers.ModelSerializer):
    """Serializer para emitir una factura. Totales y número los calcula el servidor."""

    class Meta:
        model  = Factura
        fields = ['id_pago']

    def validate(self, attrs):
        for campo in ('subtotal', 'iva', 'total', 'numero_factura', 'id_venta'):
            if campo in self.initial_data:
                raise serializers.ValidationError(
                    {campo: 'Este campo se genera automáticamente en el servidor.'},
                )
        return attrs
