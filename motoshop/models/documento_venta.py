# motoshop/models/documento_venta.py
from django.db import models
from .venta import Venta


class DocumentoVenta(models.Model):
    """Mapea exactamente la tabla 'documentos_venta' del esquema SQL."""

    TIPO_CHOICES = [
        ('contrato',     'Contrato'),
        ('factura',      'Factura'),
        ('soat',         'SOAT'),
        ('garantia',     'Garantía'),
        ('traspaso',     'Traspaso'),
        ('otro',         'Otro'),
    ]

    id_documento    = models.AutoField(primary_key=True)
    id_venta        = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        related_name='documentos',
        db_column='id_venta',
    )
    tipo_documento  = models.CharField(max_length=50, choices=TIPO_CHOICES)
    archivo_url     = models.CharField(max_length=255)
    fecha_subida    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documentos_venta'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f'Documento #{self.id_documento} — {self.tipo_documento} (Venta #{self.id_venta_id})'
