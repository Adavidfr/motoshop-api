# motoshop/models/pago.py
from django.db import models
from .venta import Venta


class Pago(models.Model):
    """Mapea exactamente la tabla 'pagos' del esquema SQL."""

    METODO_CHOICES = [
        ('efectivo',       'Efectivo'),
        ('tarjeta',        'Tarjeta'),
        ('transferencia',  'Transferencia'),
        ('credito',        'Crédito'),
        ('otro',           'Otro'),
    ]

    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente'),
        ('completado', 'Completado'),
        ('fallido',    'Fallido'),
        ('reembolsado','Reembolsado'),
    ]

    id_pago      = models.AutoField(primary_key=True)
    id_venta     = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        related_name='pagos',
        db_column='id_venta',
    )
    monto        = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago  = models.CharField(max_length=50, choices=METODO_CHOICES)
    estado       = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='pendiente')
    fecha_pago   = models.DateTimeField(auto_now_add=True)
    referencia   = models.CharField(max_length=150, blank=True, default='')

    class Meta:
        db_table = 'pagos'
        ordering = ['-fecha_pago']

    def __str__(self):
        return f'Pago #{self.id_pago} — Venta #{self.id_venta_id} ({self.estado})'
