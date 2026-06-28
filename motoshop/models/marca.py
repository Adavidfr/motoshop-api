from django.db import models

class Marca(models.Model):
    id_marca = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)

    class Meta:
        db_table = 'marcas'
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'

    def __str__(self):
        return self.nombre
