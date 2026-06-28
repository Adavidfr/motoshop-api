from django.db import models
from django.conf import settings
from .moto import Moto
from .repuesto import Repuesto

class MovimientoInventario(models.Model):
    id_movimiento = models.AutoField(primary_key=True)
    moto = models.ForeignKey(
        Moto, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='movimientos', 
        db_column='id_moto'
    )
    repuesto = models.ForeignKey(
        Repuesto, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='movimientos', 
        db_column='id_repuesto'
    )
    cantidad = models.IntegerField()
    tipo_movimiento = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='movimientos_inventario', 
        db_column='id_usuario'
    )

    class Meta:
        db_table = 'movimientos_inventario'
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'

    def __str__(self):
        item = self.moto.modelo if self.moto else (self.repuesto.nombre if self.repuesto else "N/A")
        return f"{self.tipo_movimiento.upper()} - {self.cantidad} unidades de {item}"
