# motoshop/models/carrito_compras.py
from django.db import models
from django.contrib.auth.models import User


class CarritoCompras(models.Model):
    """Mapea exactamente la tabla 'carrito_compras' del esquema SQL."""

    ESTADO_CHOICES = [
        ('activo',     'Activo'),
        ('procesado',  'Procesado'),
        ('abandonado', 'Abandonado'),
    ]

    id_carrito         = models.BigAutoField(primary_key=True)
    id_usuario_cliente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='carritos',
        db_column='id_usuario_cliente',
    )
    estado             = models.CharField(
        max_length=30,
        choices=ESTADO_CHOICES,
        default='activo',
    )
    fecha_creacion     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'carrito_compras'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'Carrito #{self.id_carrito} — {self.id_usuario_cliente.username} ({self.estado})'

    def calcular_total(self):
        """Suma de subtotales de todos los ítems del carrito."""
        return sum(item.subtotal for item in self.items.all())
