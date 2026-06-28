from rest_framework import serializers
from motoshop.models.marca import Marca

class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = '__all__'
