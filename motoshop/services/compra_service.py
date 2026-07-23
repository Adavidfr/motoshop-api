"""Lógica de negocio de compras a proveedores."""

from django.db import transaction

from motoshop.models import Compra
from motoshop.services.exceptions import BusinessError
from motoshop.services.inventario_service import InventarioService
from motoshop.services.transitions import COMPRA_TRANSICIONES, validar_transicion


class CompraService:
    @classmethod
    @transaction.atomic
    def cambiar_estado(cls, compra, nuevo_estado, usuario):
        compra = Compra.objects.select_for_update().get(pk=compra.pk)
        estado_anterior = compra.estado
        validar_transicion(estado_anterior, nuevo_estado, COMPRA_TRANSICIONES, 'compra')

        update_fields = ['estado']
        compra.estado = nuevo_estado

        if nuevo_estado == 'Recibida':
            if not compra.stock_aplicado:
                cls._aplicar_stock(compra, usuario)
                compra.stock_aplicado = True
                update_fields.append('stock_aplicado')

        compra.save(update_fields=update_fields)
        return compra

    @classmethod
    def _aplicar_stock(cls, compra, usuario):
        if not compra.moto_id and not compra.repuesto_id:
            raise BusinessError('La compra debe referenciar una moto o un repuesto.')

        desc = f'Compra #{compra.id_compra} recibida'
        if compra.moto_id:
            InventarioService.aumentar_stock(
                compra.cantidad,
                usuario,
                id_moto=compra.moto_id,
                tipo_movimiento='compra',
                descripcion=desc,
            )
        else:
            InventarioService.aumentar_stock(
                compra.cantidad,
                usuario,
                id_repuesto=compra.repuesto_id,
                tipo_movimiento='compra',
                descripcion=desc,
            )

    @classmethod
    @transaction.atomic
    def actualizar(cls, compra, usuario, **datos):
        compra = Compra.objects.select_for_update().get(pk=compra.pk)
        nuevo_estado = datos.get('estado', compra.estado)
        if nuevo_estado != compra.estado:
            return cls.cambiar_estado(compra, nuevo_estado, usuario)

        for campo, valor in datos.items():
            setattr(compra, campo, valor)
        compra.save()
        return compra
