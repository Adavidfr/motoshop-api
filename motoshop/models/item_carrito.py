# motoshop/models/item_carrito.py
from django.db import models
from .carrito_compras import CarritoCompras


class ItemCarrito(models.Model):
    """Mapea exactamente la tabla 'items_carrito' del esquema SQL."""

    id_item         = models.BigAutoField(primary_key=True)
    id_carrito      = models.ForeignKey(
        CarritoCompras,
        on_delete=models.CASCADE,
        related_name='items',
        db_column='id_carrito',
    )
    id_moto         = models.IntegerField(null=True, blank=True)
    id_repuesto     = models.IntegerField(null=True, blank=True)
    cantidad        = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal        = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'items_carrito'

    def save(self, *args, **kwargs):
        self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)

    def __str__(self):
        tipo = f'moto #{self.id_moto}' if self.id_moto else f'repuesto #{self.id_repuesto}'
        return f'{self.cantidad}x {tipo}'
