# motoshop/serializers/factura.py
from rest_framework import serializers
from motoshop.models import Factura


class FacturaSerializer(serializers.ModelSerializer):
    """Serializer de facturas con nombres exactos del esquema SQL."""

    class Meta:
        model  = Factura
        fields = [
            'id_factura', 'id_venta',
            'numero_factura', 'fecha_emision',
            'subtotal', 'iva', 'total',
        ]
        read_only_fields = ['id_factura', 'fecha_emision']

    def validate(self, attrs):
        subtotal = attrs.get('subtotal', 0)
        iva      = attrs.get('iva', 0)
        total    = attrs.get('total', 0)
        if subtotal <= 0:
            raise serializers.ValidationError({'subtotal': 'El subtotal debe ser mayor a 0.'})
        if iva < 0:
            raise serializers.ValidationError({'iva': 'El IVA no puede ser negativo.'})
        expected = round(subtotal + iva, 2)
        if round(float(total), 2) != expected:
            raise serializers.ValidationError(
                {'total': f'El total debe ser igual a subtotal + iva ({expected}).'}
            )
        return attrs


class FacturaCreateSerializer(serializers.ModelSerializer):
    """Serializer para emitir una factura."""

    class Meta:
        model  = Factura
        fields = ['id_venta', 'numero_factura', 'subtotal', 'iva', 'total']
