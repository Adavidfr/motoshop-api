# motoshop/models/garantia.py
from django.db import models
from .venta import Venta


class Garantia(models.Model):
    """Mapea exactamente la tabla 'garantias' del esquema SQL."""

    ESTADO_CHOICES = [
        ('activa',   'Activa'),
        ('vencida',  'Vencida'),
        ('anulada',  'Anulada'),
    ]

    id_garantia      = models.AutoField(primary_key=True)
    id_venta         = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        related_name='garantias',
        db_column='id_venta',
    )
    id_moto          = models.IntegerField()
    meses_garantia   = models.IntegerField()
    fecha_inicio     = models.DateField()
    fecha_fin        = models.DateField()
    descripcion      = models.TextField(blank=True, default='')
    estado           = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='activa')

    class Meta:
        db_table = 'garantias'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f'Garantia #{self.id_garantia} — Venta #{self.id_venta_id} ({self.estado})'
