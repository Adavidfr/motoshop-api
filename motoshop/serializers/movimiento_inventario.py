from rest_framework import serializers
from motoshop.models.movimiento_inventario import MovimientoInventario
from .moto import MotoSerializer
from .repuesto import RepuestoSerializer
from motoshop.serializers.user import UserSerializer

class MovimientoInventarioSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.moto:
            representation['moto'] = MotoSerializer(instance.moto).data
        if instance.repuesto:
            representation['repuesto'] = RepuestoSerializer(instance.repuesto).data
        if instance.usuario:
            representation['usuario'] = UserSerializer(instance.usuario).data
        return representation
