from rest_framework import serializers
from motoshop.models.repuesto import Repuesto

class RepuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repuesto
        fields = '__all__'
