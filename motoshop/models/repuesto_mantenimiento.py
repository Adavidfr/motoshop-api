from django.db import models
from .mantenimiento import Mantenimiento
from .repuesto import Repuesto


class RepuestoMantenimiento(models.Model):
    id_repuesto_mantenimiento = models.AutoField(primary_key=True)

    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE,
        related_name='repuestos',
        db_column='id_mantenimiento'
    )

    repuesto = models.ForeignKey(
        Repuesto,
        on_delete=models.PROTECT,
        related_name='mantenimientos',
        db_column='id_repuesto'
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

    class Meta:
        db_table = "repuestos_mantenimiento"
        verbose_name = "Repuesto de mantenimiento"
        verbose_name_plural = "Repuestos de mantenimiento"

    def __str__(self):
        return f"{self.repuesto.nombre} - {self.cantidad}"