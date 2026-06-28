# motoshop/models/devolucion.py
from django.db import models
from .venta import Venta


class Devolucion(models.Model):
    """Mapea exactamente la tabla 'devoluciones' del esquema SQL."""

    ESTADO_CHOICES = [
        ('solicitada', 'Solicitada'),
        ('aprobada',   'Aprobada'),
        ('rechazada',  'Rechazada'),
        ('completada', 'Completada'),
    ]

    id_devolucion      = models.AutoField(primary_key=True)
    id_venta           = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        related_name='devoluciones',
        db_column='id_venta',
    )
    motivo             = models.TextField()
    estado             = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='solicitada')
    monto_devolucion   = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_solicitud    = models.DateTimeField(auto_now_add=True)
    fecha_resolucion   = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'devoluciones'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f'Devolucion #{self.id_devolucion} — Venta #{self.id_venta_id} ({self.estado})'
