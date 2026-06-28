from rest_framework import serializers
from motoshop.models.categoria_moto import CategoriaMoto

class CategoriaMotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaMoto
        fields = '__all__'
