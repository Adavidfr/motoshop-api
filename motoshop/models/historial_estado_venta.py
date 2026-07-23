# motoshop/models/historial_estado_venta.py
from django.conf import settings
from django.db import models
from .venta import Venta


class HistorialEstadoVenta(models.Model):
    """Mapea exactamente la tabla 'historial_estado_venta' del esquema SQL."""

    id_historial    = models.AutoField(primary_key=True)
    id_venta        = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='historial_estados',
        db_column='id_venta',
    )
    estado_anterior = models.CharField(max_length=30)
    estado_nuevo    = models.CharField(max_length=30)
    fecha_cambio    = models.DateTimeField(auto_now_add=True)
    observacion     = models.TextField(blank=True, default='')
    id_usuario      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historial_ventas_registradas',
        db_column='id_usuario',
    )

    class Meta:
        db_table = 'historial_estado_venta'
        ordering = ['-fecha_cambio']

    def __str__(self):
        return (
            f'Historial #{self.id_historial} — Venta #{self.id_venta_id} '
            f'({self.estado_anterior} → {self.estado_nuevo})'
        )
