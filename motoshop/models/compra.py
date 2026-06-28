from django.db import models
from .proveedor import Proveedor
from .moto import Moto
from .repuesto import Repuesto


class Compra(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('Recibida', 'Recibida'),
        ('Cancelada', 'Cancelada'),
    ]

    id_compra = models.AutoField(primary_key=True)

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='compras',
        db_column='id_proveedor'
    )

    moto = models.ForeignKey(
        Moto,
        on_delete=models.PROTECT,
        related_name='compras',
        db_column='id_moto',
        null=True,
        blank=True
    )

    repuesto = models.ForeignKey(
        Repuesto,
        on_delete=models.PROTECT,
        related_name='compras',
        db_column='id_repuesto',
        null=True,
        blank=True
    )

    cantidad = models.PositiveIntegerField()

    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    fecha_compra = models.DateTimeField(auto_now_add=True)

    estado = models.CharField(
        max_length=30,
        choices=ESTADOS,
        default='Pendiente'
    )

    class Meta:
        db_table = "compras"
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ["-fecha_compra"]

    def __str__(self):
        return f"Compra #{self.id_compra}"