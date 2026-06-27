from rest_framework import serializers
from motoshop.models.moto import Moto
from .marca import MarcaSerializer
from .categoria_moto import CategoriaMotoSerializer

class MotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moto
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['marca'] = MarcaSerializer(instance.marca).data
        representation['categoria'] = CategoriaMotoSerializer(instance.categoria).data
        return representation
