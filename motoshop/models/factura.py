# motoshop/models/factura.py
from django.db import models
from .venta import Venta


class Factura(models.Model):
    """Mapea exactamente la tabla 'facturas' del esquema SQL."""

    id_factura      = models.AutoField(primary_key=True)
    id_venta        = models.OneToOneField(
        Venta,
        on_delete=models.PROTECT,
        related_name='factura',
        db_column='id_venta',
    )
    numero_factura  = models.CharField(max_length=50, unique=True)
    fecha_emision   = models.DateTimeField(auto_now_add=True)
    subtotal        = models.DecimalField(max_digits=12, decimal_places=2)
    iva             = models.DecimalField(max_digits=12, decimal_places=2)
    total           = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'facturas'
        ordering = ['-fecha_emision']

    def __str__(self):
        return f'Factura #{self.numero_factura} — Venta #{self.id_venta_id}'
