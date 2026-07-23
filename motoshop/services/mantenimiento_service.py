"""Lógica de negocio de mantenimiento en taller."""

from django.db import transaction

from motoshop.models import Mantenimiento, RepuestoMantenimiento
from motoshop.services.exceptions import BusinessError
from motoshop.services.inventario_service import InventarioService
from motoshop.services.notificacion_service import NotificacionService
from motoshop.services.transitions import MANTENIMIENTO_TRANSICIONES, validar_transicion


class MantenimientoService:
    @classmethod
    @transaction.atomic
    def cambiar_estado(cls, mantenimiento, nuevo_estado, actor):
        mantenimiento = Mantenimiento.objects.select_for_update().get(pk=mantenimiento.pk)
        validar_transicion(
            mantenimiento.estado, nuevo_estado, MANTENIMIENTO_TRANSICIONES, 'mantenimiento',
        )

        if nuevo_estado == 'Finalizado':
            cls._finalizar(mantenimiento, actor)
        else:
            mantenimiento.estado = nuevo_estado
            mantenimiento.save(update_fields=['estado'])

        return mantenimiento

    @classmethod
    def _finalizar(cls, mantenimiento, actor):
        if mantenimiento.repuestos_descontados:
            raise BusinessError('Los repuestos de este mantenimiento ya fueron descontados.')

        repuestos = RepuestoMantenimiento.objects.filter(
            mantenimiento=mantenimiento,
        ).select_related('repuesto')

        for rm in repuestos:
            InventarioService.disminuir_stock(
                rm.cantidad,
                actor,
                id_repuesto=rm.repuesto_id,
                tipo_movimiento='mantenimiento',
                descripcion=(
                    f'Mantenimiento #{mantenimiento.id_mantenimiento} — '
                    f'repuesto #{rm.repuesto_id}'
                ),
            )

        mantenimiento.estado = 'Finalizado'
        mantenimiento.repuestos_descontados = True
        mantenimiento.save(update_fields=['estado', 'repuestos_descontados'])
        NotificacionService.mantenimiento_finalizado(mantenimiento)
