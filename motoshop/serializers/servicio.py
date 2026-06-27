# motoshop/serializers/servicio.py

from rest_framework import serializers
from motoshop.models import Servicio


class ServicioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Servicio
        fields = [
            'id',
            'nombre',
            'descripcion',
            'precio_base',
            'tiempo_estimado_minutos',
            'estado',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = [
            'id',
            'fecha_creacion',
            'fecha_actualizacion',
        ]

    def validate_nombre(self, value):
        qs = Servicio.objects.filter(nombre__iexact=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                'Ya existe un servicio con ese nombre.'
            )

        return value