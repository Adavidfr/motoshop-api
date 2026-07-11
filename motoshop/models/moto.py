from django.db import models
from .categoria_moto import CategoriaMoto
from .marca import Marca

class Moto(models.Model):
    id_moto = models.AutoField(primary_key=True)
    categoria = models.ForeignKey(
        CategoriaMoto, 
        on_delete=models.PROTECT, 
        related_name='motos', 
        db_column='id_categoria'
    )
    marca = models.ForeignKey(
        Marca, 
        on_delete=models.PROTECT, 
        related_name='motos', 
        db_column='id_marca'
    )
    modelo = models.CharField(max_length=150)
    anio = models.IntegerField()
    cilindraje = models.IntegerField()
    color = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.IntegerField()
    estado = models.CharField(max_length=30)
    imagen = models.ImageField(upload_to='motos/', null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'motos'
        verbose_name = 'Moto'
        verbose_name_plural = 'Motos'

    def __str__(self):
        return f"{self.marca.nombre} {self.modelo} ({self.anio})"
