from django.db import models

class CategoriaMoto(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = 'categorias_moto'
        verbose_name = 'Categoría de Moto'
        verbose_name_plural = 'Categorías de Motos'

    def __str__(self):
        return self.nombre
