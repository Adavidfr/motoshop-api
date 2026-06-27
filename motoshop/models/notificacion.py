# motoshop/models/notificacion.py
from django.db import models
from django.contrib.auth.models import User


class Notificacion(models.Model):
    """Mapea exactamente la tabla 'notificaciones' del esquema SQL."""

    id_notificacion = models.AutoField(primary_key=True)
    id_usuario      = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        db_column='id_usuario',
    )
    titulo          = models.CharField(max_length=150)
    mensaje         = models.TextField()
    leido           = models.BooleanField(default=False)
    fecha_creacion  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'Notificacion #{self.id_notificacion} — {self.id_usuario.username} ({"leída" if self.leido else "no leída"})'
