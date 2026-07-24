# motoshop/serializers/pago.py
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from motoshop.models import Pago, Financiamiento


class PagoFacturaResumenSerializer(serializers.Serializer):
    """Resumen ligero de la factura vinculada al pago (0..1)."""
    id_factura = serializers.IntegerField()
    numero_factura = serializers.CharField()


class PagoSerializer(serializers.ModelSerializer):
    """Serializer de pagos con nombres exactos del esquema SQL."""
    procesado_por_info = serializers.SerializerMethodField()
    factura = serializers.SerializerMethodField()

    class Meta:
        model  = Pago
        fields = [
            'id_pago', 'id_venta', 'id_financiamiento',
            'monto', 'metodo_pago', 'tipo_pago', 'estado',
            'fecha_pago', 'referencia', 'comprobante',
            'procesado_por', 'procesado_por_info', 'factura',
        ]
        read_only_fields = ['id_pago', 'fecha_pago', 'procesado_por', 'procesado_por_info', 'factura']

    def get_procesado_por_info(self, obj):
        if not obj.procesado_por_id:
            return None
        return {'id': obj.procesado_por_id, 'username': obj.procesado_por.username}

    def get_factura(self, obj):
        try:
            factura = obj.factura
        except ObjectDoesNotExist:
            return None
        if factura is None:
            return None
        return PagoFacturaResumenSerializer(factura).data


class PagoCreateSerializer(serializers.ModelSerializer):
    """Serializer para registrar un nuevo pago (validación de formato)."""

    id_financiamiento = serializers.PrimaryKeyRelatedField(
        queryset=Financiamiento.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model  = Pago
        fields = [
            'id_venta', 'id_financiamiento',
            'monto', 'metodo_pago', 'tipo_pago', 'estado',
            'referencia', 'comprobante',
        ]

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError('El monto del pago debe ser mayor a 0.')
        return value
