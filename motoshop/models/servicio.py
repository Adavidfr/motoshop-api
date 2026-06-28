from django.db import models


class Servicio(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    precio_base = models.DecimalField(max_digits=12, decimal_places=2)
    tiempo_estimado_minutos = models.IntegerField()
    estado = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "servicios"
        ordering = ["nombre"]
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return self.nombre