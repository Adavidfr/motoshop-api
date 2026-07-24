# motoshop/serializers/venta.py
from rest_framework import serializers
from motoshop.models import Venta, Pedido
from motoshop.serializers.financiamiento import FinanciamientoSerializer
from motoshop.serializers.pago import PagoSerializer
from motoshop.serializers.factura import FacturaSerializer
from motoshop.serializers.pedido import PedidoSerializer
from motoshop.services.venta_service import VentaService


class VentaSerializer(serializers.ModelSerializer):
    """Serializer de ventas con nombres exactos del esquema SQL."""
    financiamientos     = FinanciamientoSerializer(many=True, read_only=True)
    username_cliente    = serializers.CharField(
        source='id_usuario_cliente.username', read_only=True,
    )
    username_vendedor   = serializers.CharField(
        source='id_usuario_vendedor.username', read_only=True,
    )
    procesado_por       = serializers.SerializerMethodField()
    num_financiamientos = serializers.SerializerMethodField()
    total_pagado        = serializers.SerializerMethodField()
    saldo_pendiente     = serializers.SerializerMethodField()

    class Meta:
        model  = Venta
        fields = [
            'id_venta', 'id_pedido',
            'username_cliente', 'id_usuario_cliente',
            'username_vendedor', 'id_usuario_vendedor', 'procesado_por',
            'total_venta', 'total_pagado', 'saldo_pendiente',
            'estado', 'fecha_venta',
            'num_financiamientos', 'financiamientos',
        ]
        read_only_fields = [
            'id_venta', 'fecha_venta', 'total_venta',
            'total_pagado', 'saldo_pendiente',
            'username_cliente', 'id_usuario_cliente',
            'username_vendedor', 'id_usuario_vendedor', 'procesado_por',
        ]

    def get_procesado_por(self, obj):
        if not obj.id_usuario_vendedor_id:
            return None
        return {
            'id': obj.id_usuario_vendedor_id,
            'username': obj.id_usuario_vendedor.username,
        }

    def get_num_financiamientos(self, obj):
        return obj.financiamientos.count()

    def get_total_pagado(self, obj):
        return float(VentaService.total_pagado(obj))

    def get_saldo_pendiente(self, obj):
        return float(VentaService.saldo_pendiente(obj))


class VentaDetailSerializer(VentaSerializer):
    pedido         = PedidoSerializer(source='id_pedido', read_only=True)
    pagos          = PagoSerializer(many=True, read_only=True)
    financiamiento = serializers.SerializerMethodField()
    facturas       = serializers.SerializerMethodField()

    class Meta(VentaSerializer.Meta):
        fields = VentaSerializer.Meta.fields + [
            'pedido', 'pagos', 'financiamiento', 'facturas',
        ]

    def get_financiamiento(self, obj):
        f = obj.financiamientos.first()
        return FinanciamientoSerializer(f).data if f else None

    def get_facturas(self, obj):
        from motoshop.models import Factura
        facturas = Factura.objects.filter(id_pago__id_venta=obj).select_related('id_pago')
        return FacturaSerializer(facturas, many=True).data


class VentaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para registrar una venta desde un pedido confirmado.
    Body: { "id_pedido": 1, "estado": "pendiente" }
    El total se calcula en backend; total_venta del frontend se ignora.
    """
    id_pedido = serializers.PrimaryKeyRelatedField(queryset=Pedido.objects.all())

    class Meta:
        model  = Venta
        fields = ['id_pedido', 'estado']

    def validate(self, attrs):
        if 'total_venta' in self.initial_data:
            raise serializers.ValidationError(
                {'total_venta': 'El total se calcula automáticamente en el servidor.'},
            )
        return attrs
