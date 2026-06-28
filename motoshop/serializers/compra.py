from rest_framework import serializers
from motoshop.models import Compra


class CompraSerializer(serializers.ModelSerializer):

    class Meta:
        model = Compra
        fields = [
            'id_compra',
            'proveedor',
            'moto',
            'repuesto',
            'cantidad',
            'precio_unitario',
            'subtotal',
            'fecha_compra',
            'estado',
        ]
        read_only_fields = [
            'id_compra',
            'fecha_compra',
        ]

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "La cantidad debe ser mayor que cero."
            )
        return value

    def validate_precio_unitario(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El precio unitario debe ser mayor que cero."
            )
        return value

    def validate(self, data):
        moto = data.get('moto', getattr(self.instance, 'moto', None))
        repuesto = data.get('repuesto', getattr(self.instance, 'repuesto', None))

        if not moto and not repuesto:
            raise serializers.ValidationError(
                "Debe seleccionar una moto o un repuesto."
            )

        if moto and repuesto:
            raise serializers.ValidationError(
                "Solo puede seleccionar una moto o un repuesto."
            )

        return data