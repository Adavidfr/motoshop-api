# motoshop/models/financiamiento.py
from django.db import models
from .venta import Venta


class Financiamiento(models.Model):
    """Mapea exactamente la tabla 'financiamientos' del esquema SQL."""

    ESTADO_CHOICES = [
        ('activo',    'Activo'),
        ('pagado',    'Pagado'),
        ('vencido',   'Vencido'),
        ('cancelado', 'Cancelado'),
    ]

    id_financiamiento  = models.BigAutoField(primary_key=True)
    id_venta           = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        related_name='financiamientos',
        db_column='id_venta',
    )
    entidad_financiera = models.CharField(max_length=100)
    monto_financiado   = models.DecimalField(max_digits=12, decimal_places=2)
    tasa_interes       = models.DecimalField(max_digits=5,  decimal_places=2)
    plazo_meses        = models.PositiveIntegerField()
    cuota_mensual      = models.DecimalField(max_digits=12, decimal_places=2)
    estado             = models.CharField(
        max_length=30,
        choices=ESTADO_CHOICES,
        default='activo',
    )

    class Meta:
        db_table = 'financiamientos'

    def __str__(self):
        return f'Financiamiento #{self.id_financiamiento} — {self.entidad_financiera} ({self.estado})'
