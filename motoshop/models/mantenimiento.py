from django.db import models
from django.contrib.auth.models import User

from .moto import Moto
from .servicio import Servicio


class Mantenimiento(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('En proceso', 'En proceso'),
        ('Finalizado', 'Finalizado'),
        ('Cancelado', 'Cancelado'),
    ]

    id_mantenimiento = models.AutoField(primary_key=True)

    moto = models.ForeignKey(
        Moto,
        on_delete=models.PROTECT,
        related_name='mantenimientos',
        db_column='id_moto'
    )

    usuario_cliente = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='mantenimientos',
        db_column='id_usuario_cliente'
    )

    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name='mantenimientos',
        db_column='id_servicio'
    )

    kilometraje_actual = models.PositiveIntegerField()
    diagnostico_inicial = models.TextField(blank=True, null=True)

    costo_final = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    estado = models.CharField(
        max_length=50,
        choices=ESTADOS,
        default='Pendiente'
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mantenimientos"
        verbose_name = "Mantenimiento"
        verbose_name_plural = "Mantenimientos"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"Mantenimiento #{self.id_mantenimiento} - {self.moto}"