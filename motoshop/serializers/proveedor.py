from rest_framework import serializers
from motoshop.models import Proveedor


class ProveedorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Proveedor
        fields = ['id','nombre','contacto','telefono','correo','direccion','estado',]
        read_only_fields = ['id']

    def validate_nombre(self, value):
        qs = Proveedor.objects.filter(nombre__iexact=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                'Ya existe un proveedor con ese nombre.'
            )

        return value

    def validate_correo(self, value):
        if value:
            qs = Proveedor.objects.filter(correo__iexact=value)

            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError(
                    'Ya existe un proveedor con ese correo.'
                )

        return value