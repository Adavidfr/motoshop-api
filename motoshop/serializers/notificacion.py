# motoshop/serializers/notificacion.py
from rest_framework import serializers
from motoshop.models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    """Serializer de notificaciones con nombres exactos del esquema SQL."""

    class Meta:
        model  = Notificacion
        fields = [
            'id_notificacion', 'id_usuario',
            'titulo', 'mensaje', 'leido', 'fecha_creacion',
        ]
        read_only_fields = ['id_notificacion', 'fecha_creacion', 'id_usuario']


class NotificacionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear una notificación (el id_usuario se asigna en la vista)."""

    class Meta:
        model  = Notificacion
        fields = ['id_usuario', 'titulo', 'mensaje']
