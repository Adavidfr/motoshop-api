# motoshop/models/cliente.py
from django.db import models
from django.contrib.auth.models import User


class ClientePerfil(models.Model):
    """Mapea exactamente la tabla 'clientes_perfil' del esquema SQL."""

    id_perfil        = models.BigAutoField(primary_key=True)
    id_usuario       = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil_cliente',
        db_column='id_usuario',
    )
    cedula           = models.CharField(max_length=20, blank=True, default='')
    telefono         = models.CharField(max_length=20, blank=True, default='')
    direccion        = models.TextField(blank=True, default='')
    fecha_nacimiento = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'clientes_perfil'

    def __str__(self):
        return f'Perfil de {self.id_usuario.username}'
