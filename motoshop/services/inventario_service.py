"""Servicio centralizado de inventario y movimientos."""

from django.db import transaction

from motoshop.models import MovimientoInventario
from motoshop.models.moto import Moto
from motoshop.models.repuesto import Repuesto
from motoshop.services.exceptions import BusinessError
from motoshop.utils.inventario import (
    resolver_producto,
    validar_stock_carrito,
    validar_stock_solicitado,
)


class InventarioService:
    """Ajustes de stock con bloqueo y registro de movimientos."""

    @staticmethod
    def _bloquear_producto(id_moto=None, id_repuesto=None):
        if id_moto:
            try:
                return Moto.objects.select_for_update().get(pk=id_moto), None
            except Moto.DoesNotExist:
                raise BusinessError('La moto no existe.', field='id_moto')
        try:
            return None, Repuesto.objects.select_for_update().get(pk=id_repuesto)
        except Repuesto.DoesNotExist:
            raise BusinessError('El repuesto no existe.', field='id_repuesto')

    @classmethod
    @transaction.atomic
    def aumentar_stock(
        cls,
        cantidad,
        usuario,
        id_moto=None,
        id_repuesto=None,
        tipo_movimiento='entrada',
        descripcion='',
    ):
        if cantidad <= 0:
            raise BusinessError('La cantidad a aumentar debe ser mayor a cero.')

        moto, repuesto = cls._bloquear_producto(id_moto, id_repuesto)

        if moto:
            moto.stock += cantidad
            if moto.estado != 'disponible' and moto.stock > 0:
                moto.estado = 'disponible'
            moto.save(update_fields=['stock', 'estado'])
            producto_moto, producto_repuesto = moto, None
        else:
            repuesto.stock += cantidad
            repuesto.save(update_fields=['stock'])
            producto_moto, producto_repuesto = None, repuesto

        return MovimientoInventario.objects.create(
            moto=producto_moto,
            repuesto=producto_repuesto,
            cantidad=cantidad,
            tipo_movimiento=tipo_movimiento,
            descripcion=descripcion,
            usuario=usuario,
        )

    @classmethod
    @transaction.atomic
    def disminuir_stock(
        cls,
        cantidad,
        usuario,
        id_moto=None,
        id_repuesto=None,
        tipo_movimiento='salida',
        descripcion='',
    ):
        if cantidad <= 0:
            raise BusinessError('La cantidad a disminuir debe ser mayor a cero.')

        moto, repuesto = cls._bloquear_producto(id_moto, id_repuesto)

        if moto:
            if moto.stock < cantidad:
                raise BusinessError(
                    f'Stock insuficiente para {moto.modelo}. '
                    f'Disponible: {moto.stock}, solicitado: {cantidad}.',
                )
            moto.stock -= cantidad
            if moto.stock == 0:
                moto.estado = 'vendida'
            moto.save(update_fields=['stock', 'estado'])
            producto_moto, producto_repuesto = moto, None
        else:
            if repuesto.stock < cantidad:
                raise BusinessError(
                    f'Stock insuficiente para {repuesto.nombre}. '
                    f'Disponible: {repuesto.stock}, solicitado: {cantidad}.',
                )
            repuesto.stock -= cantidad
            repuesto.save(update_fields=['stock'])
            producto_moto, producto_repuesto = None, repuesto

        return MovimientoInventario.objects.create(
            moto=producto_moto,
            repuesto=producto_repuesto,
            cantidad=-cantidad,
            tipo_movimiento=tipo_movimiento,
            descripcion=descripcion,
            usuario=usuario,
        )

    @classmethod
    def disminuir_por_carrito(cls, carrito, usuario, referencia=''):
        """Descuenta stock de todos los ítems de un carrito."""
        validar_stock_carrito(carrito)
        movimientos = []
        for item in carrito.items.all():
            desc = f'{referencia} — ítem #{item.id_item}'
            if item.id_moto:
                mov = cls.disminuir_stock(
                    item.cantidad,
                    usuario,
                    id_moto=item.id_moto,
                    tipo_movimiento='venta',
                    descripcion=desc,
                )
            else:
                mov = cls.disminuir_stock(
                    item.cantidad,
                    usuario,
                    id_repuesto=item.id_repuesto,
                    tipo_movimiento='venta',
                    descripcion=desc,
                )
            movimientos.append(mov)
        return movimientos

    @classmethod
    def reintegrar_por_carrito(cls, carrito, usuario, referencia=''):
        """Reintegra stock de todos los ítems (devolución aprobada)."""
        movimientos = []
        for item in carrito.items.all():
            desc = f'{referencia} — ítem #{item.id_item}'
            if item.id_moto:
                mov = cls.aumentar_stock(
                    item.cantidad,
                    usuario,
                    id_moto=item.id_moto,
                    tipo_movimiento='devolucion',
                    descripcion=desc,
                )
            else:
                mov = cls.aumentar_stock(
                    item.cantidad,
                    usuario,
                    id_repuesto=item.id_repuesto,
                    tipo_movimiento='devolucion',
                    descripcion=desc,
                )
            movimientos.append(mov)
        return movimientos

    # Delegación de validaciones usadas por serializers
    resolver_producto = staticmethod(resolver_producto)
    validar_stock_solicitado = staticmethod(validar_stock_solicitado)
    validar_stock_carrito = staticmethod(validar_stock_carrito)
