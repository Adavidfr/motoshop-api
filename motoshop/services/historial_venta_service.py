"""Registro append-only del historial de estados de venta."""

from django.db import transaction

from motoshop.models import HistorialEstadoVenta
from motoshop.services.exceptions import BusinessError
from motoshop.services.notificacion_service import NotificacionService
from motoshop.services.transitions import VENTA_TRANSICIONES, validar_transicion


class HistorialVentaService:
    @staticmethod
    def registrar(venta, estado_anterior, estado_nuevo, actor=None, observacion=''):
        return HistorialEstadoVenta.objects.create(
            id_venta=venta,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            observacion=observacion,
            id_usuario=actor,
        )

    @classmethod
    @transaction.atomic
    def cambiar_estado_venta(cls, venta, nuevo_estado, actor=None, observacion='', notificar=True):
        estado_anterior = venta.estado
        validar_transicion(estado_anterior, nuevo_estado, VENTA_TRANSICIONES, 'venta')

        venta.estado = nuevo_estado
        venta.save(update_fields=['estado'])

        cls.registrar(venta, estado_anterior, nuevo_estado, actor, observacion)

        if notificar and venta.id_usuario_cliente_id:
            NotificacionService.estado_venta_actualizado(venta, estado_anterior, observacion)

        return venta
