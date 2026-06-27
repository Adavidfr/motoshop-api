# motoshop/models/seguro.py
from django.db import models
from .venta import Venta


class Seguro(models.Model):
    """Mapea exactamente la tabla 'seguros' del esquema SQL."""

    ESTADO_CHOICES = [
        ('activo',   'Activo'),
        ('vencido',  'Vencido'),
        ('cancelado','Cancelado'),
    ]

    id_seguro        = models.AutoField(primary_key=True)
    id_venta         = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        related_name='seguros',
        db_column='id_venta',
    )
    aseguradora      = models.CharField(max_length=100)
    numero_poliza    = models.CharField(max_length=100, unique=True)
    tipo_cobertura   = models.CharField(max_length=50)
    fecha_inicio     = models.DateField()
    fecha_fin        = models.DateField()
    costo_anual      = models.DecimalField(max_digits=12, decimal_places=2)
    estado           = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='activo')

    class Meta:
        db_table = 'seguros'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f'Seguro #{self.id_seguro} — {self.aseguradora} ({self.estado})'
