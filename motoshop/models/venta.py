# motoshop/models/venta.py
from django.db import models
from django.contrib.auth.models import User
from .pedido import Pedido


class Venta(models.Model):
    """Mapea exactamente la tabla 'ventas' del esquema SQL."""

    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente'),
        ('completada', 'Completada'),
        ('anulada',    'Anulada'),
    ]

    id_venta            = models.BigAutoField(primary_key=True)
    id_pedido           = models.OneToOneField(
        Pedido,
        on_delete=models.PROTECT,
        related_name='venta',
        db_column='id_pedido',
    )
    id_usuario_cliente  = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='ventas_como_cliente',
        db_column='id_usuario_cliente',
    )
    id_usuario_vendedor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='ventas_como_vendedor',
        db_column='id_usuario_vendedor',
    )
    total_venta         = models.DecimalField(max_digits=12, decimal_places=2)
    estado              = models.CharField(
        max_length=30,
        choices=ESTADO_CHOICES,
        default='pendiente',
    )
    fecha_venta         = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ventas'
        ordering = ['-fecha_venta']

    def __str__(self):
        return f'Venta #{self.id_venta} — Pedido #{self.id_pedido_id} ({self.estado})'
