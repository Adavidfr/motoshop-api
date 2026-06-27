from rest_framework import serializers
from motoshop.models import Mantenimiento


class MantenimientoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Mantenimiento
        fields = [
            'id_mantenimiento',
            'moto',
            'usuario_cliente',
            'servicio',
            'kilometraje_actual',
            'diagnostico_inicial',
            'costo_final',
            'estado',
            'fecha_registro',
        ]
        read_only_fields = [
            'id_mantenimiento',
            'fecha_registro',
        ]

    def validate_kilometraje_actual(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "El kilometraje no puede ser negativo."
            )
        return value

    def validate_costo_final(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "El costo final no puede ser negativo."
            )
        return value