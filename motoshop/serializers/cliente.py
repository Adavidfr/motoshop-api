# motoshop/serializers/cliente.py
from rest_framework import serializers
from motoshop.models import ClientePerfil


class ClientePerfilSerializer(serializers.ModelSerializer):
    """Serializer de clientes_perfil con nombres exactos del esquema SQL."""
    username = serializers.CharField(source='id_usuario.username', read_only=True)
    email    = serializers.CharField(source='id_usuario.email',    read_only=True)

    class Meta:
        model  = ClientePerfil
        fields = [
            'id_perfil', 'username', 'email',
            'cedula', 'telefono', 'direccion', 'fecha_nacimiento',
        ]
        read_only_fields = ['id_perfil', 'username', 'email']
