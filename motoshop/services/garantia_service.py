"""Lógica de negocio de garantías."""

from django.db import transaction
from django.utils import timezone

from motoshop.models import Garantia
from motoshop.models.moto import Moto
from motoshop.services.exceptions import BusinessError
from motoshop.services.transitions import GARANTIA_TRANSICIONES, validar_transicion


class GarantiaService:
    @staticmethod
    def _moto_en_venta(venta, moto_id):
        carrito = venta.id_pedido.id_carrito if venta.id_pedido_id else None
        if not carrito:
            return False
        return carrito.items.filter(id_moto=moto_id).exists()

    @classmethod
    @transaction.atomic
    def crear(cls, venta, moto_id, meses_garantia, fecha_inicio, fecha_fin,
              descripcion='', estado='activa'):
        try:
            moto = Moto.objects.get(pk=moto_id)
        except Moto.DoesNotExist:
            raise BusinessError('La moto no existe.', field='id_moto')

        if not cls._moto_en_venta(venta, moto_id):
            raise BusinessError(
                'La moto debe pertenecer a los ítems de la venta.',
                field='id_moto',
            )
        if fecha_fin <= fecha_inicio:
            raise BusinessError(
                'La fecha de fin debe ser posterior a la fecha de inicio.',
                field='fecha_fin',
            )

        return Garantia.objects.create(
            id_venta=venta,
            id_moto=moto,
            meses_garantia=meses_garantia,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            descripcion=descripcion,
            estado=estado,
        )

    @classmethod
    def cambiar_estado(cls, garantia, nuevo_estado):
        validar_transicion(garantia.estado, nuevo_estado, GARANTIA_TRANSICIONES, 'garantía')
        garantia.estado = nuevo_estado
        garantia.save(update_fields=['estado'])
        return garantia

    @staticmethod
    def verificar_vencidas():
        hoy = timezone.now().date()
        return Garantia.objects.filter(estado='activa', fecha_fin__lt=hoy).update(estado='vencida')
