# motoshop/models/documento_venta.py
from django.conf import settings
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
    tipo_documento      = models.CharField(max_length=50, choices=TIPO_CHOICES)
    archivo             = models.FileField(upload_to='documentos_venta/', null=True, blank=True)
    nombre_original     = models.CharField(max_length=255, blank=True, default='')
    tamano_bytes        = models.PositiveIntegerField(null=True, blank=True)
    content_type        = models.CharField(max_length=100, blank=True, default='')
    subido_por          = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_subidos',
        db_column='id_usuario_subidor',
    )
    archivo_url_legacy  = models.CharField(max_length=255, blank=True, default='')
    fecha_subida        = models.DateTimeField(auto_now_add=True)

    @property
    def archivo_url(self):
        """Compatibilidad con clientes que consumen archivo_url."""
        if self.archivo:
            return self.archivo.url
        return self.archivo_url_legacy or ''

    class Meta:
        db_table = 'documentos_venta'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f'Documento #{self.id_documento} — {self.tipo_documento} (Venta #{self.id_venta_id})'
