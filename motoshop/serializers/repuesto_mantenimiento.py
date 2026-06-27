from rest_framework import serializers
from motoshop.models import RepuestoMantenimiento


class RepuestoMantenimientoSerializer(serializers.ModelSerializer):

    class Meta:
        model = RepuestoMantenimiento
        fields = [
            'id_repuesto_mantenimiento',
            'mantenimiento',
            'repuesto',
            'cantidad',
            'precio_unitario',
            'subtotal',
        ]
        read_only_fields = [
            'id_repuesto_mantenimiento',
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