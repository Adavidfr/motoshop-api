# motoshop/models/pedido.py
from django.db import models
from django.contrib.auth.models import User
from .carrito_compras import CarritoCompras


class Pedido(models.Model):
    """Mapea exactamente la tabla 'pedidos' del esquema SQL."""

    ESTADO_CHOICES = [
        ('pending',   'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('shipped',   'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]

    id_pedido          = models.BigAutoField(primary_key=True)
    id_usuario_cliente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        db_column='id_usuario_cliente',
    )
    id_carrito         = models.ForeignKey(
        CarritoCompras,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos',
        db_column='id_carrito',
    )
    estado             = models.CharField(
        max_length=30,
        choices=ESTADO_CHOICES,
        default='pending',
    )
    total              = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_pedido       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pedidos'
        ordering = ['-fecha_pedido']

    def __str__(self):
        return f'Pedido #{self.id_pedido} — {self.id_usuario_cliente.username} ({self.estado})'

    def calculate_total(self):
        """Calcula el total desde los ítems del carrito asociado."""
        if self.id_carrito:
            self.total = self.id_carrito.calcular_total()
        self.save(update_fields=['total'])
