from django.db import models

class Repuesto(models.Model):
    id_repuesto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=50, unique=True)
    costo = models.DecimalField(max_digits=12, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.IntegerField()
    estado = models.CharField(max_length=50)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'repuestos'
        verbose_name = 'Repuesto'
        verbose_name_plural = 'Repuestos'

    def __str__(self):
        return f"{self.nombre} (SKU: {self.sku})"
