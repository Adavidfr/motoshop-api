"""Lógica de negocio del carrito de compras."""

from django.db import transaction
from rest_framework.exceptions import ValidationError as DRFValidationError

from motoshop.models import CarritoCompras, ItemCarrito, Pedido
from motoshop.services.exceptions import BusinessError
from motoshop.services.inventario_service import InventarioService
from motoshop.services.transitions import CARRITO_TERMINAL


def _validation_error_a_negocio(exc):
    detail = exc.detail
    if isinstance(detail, dict):
        val = next(iter(detail.values()))
        detail = val[0] if isinstance(val, list) else val
    elif isinstance(detail, list):
        detail = detail[0]
    raise BusinessError(str(detail))


class CarritoService:
    @staticmethod
    def obtener_activo(usuario):
        return (
            CarritoCompras.objects
            .filter(id_usuario_cliente=usuario, estado='activo')
            .prefetch_related('items')
            .first()
        )

    @classmethod
    def obtener_o_crear_activo(cls, usuario):
        carrito = cls.obtener_activo(usuario)
        if carrito:
            return carrito, False
        carrito = CarritoCompras.objects.create(id_usuario_cliente=usuario, estado='activo')
        return carrito, True

    @staticmethod
    def _validar_modificable(carrito, usuario):
        if carrito.id_usuario_cliente_id != usuario.id:
            raise BusinessError('No tienes permiso para modificar este carrito.')
        if carrito.estado in CARRITO_TERMINAL:
            raise BusinessError(
                f'No se puede modificar un carrito con estado "{carrito.estado}".',
            )

    @classmethod
    @transaction.atomic
    def agregar_item(cls, carrito, usuario, id_moto=None, id_repuesto=None, cantidad=1):
        cls._validar_modificable(carrito, usuario)

        if cantidad <= 0:
            raise BusinessError('La cantidad debe ser mayor a cero.', field='cantidad')

        if not id_moto and not id_repuesto:
            raise BusinessError('Debe indicar id_moto o id_repuesto.')
        if id_moto and id_repuesto:
            raise BusinessError('Indique solo id_moto o id_repuesto, no ambos.')

        precio, _, _ = InventarioService.resolver_producto(id_moto, id_repuesto)

        filtro = {'id_carrito': carrito}
        if id_moto:
            filtro['id_moto'] = id_moto
        else:
            filtro['id_repuesto'] = id_repuesto

        item_existente = ItemCarrito.objects.filter(**filtro).first()
        cantidad_final = cantidad + (item_existente.cantidad if item_existente else 0)

        try:
            InventarioService.validar_stock_solicitado(
                id_moto,
                id_repuesto,
                cantidad_final,
                carrito=carrito,
                exclude_item_id=item_existente.id_item if item_existente else None,
            )
        except DRFValidationError as exc:
            _validation_error_a_negocio(exc)

        if item_existente:
            item_existente.cantidad = cantidad_final
            item_existente.precio_unitario = precio
            item_existente.save()
            return item_existente

        return ItemCarrito.objects.create(
            id_carrito=carrito,
            id_moto=id_moto,
            id_repuesto=id_repuesto,
            cantidad=cantidad,
            precio_unitario=precio,
        )

    @classmethod
    @transaction.atomic
    def eliminar_item(cls, carrito, usuario, item_id):
        cls._validar_modificable(carrito, usuario)
        try:
            item = ItemCarrito.objects.get(id_item=item_id, id_carrito=carrito)
        except ItemCarrito.DoesNotExist:
            raise BusinessError('Ítem no encontrado en este carrito.')
        item.delete()
        return carrito

    @classmethod
    @transaction.atomic
    def vaciar(cls, carrito, usuario):
        cls._validar_modificable(carrito, usuario)
        carrito.items.all().delete()
        return carrito

    @staticmethod
    def marcar_procesado(carrito):
        if carrito.estado != 'activo':
            raise BusinessError(
                f'Solo se puede procesar un carrito activo. Estado actual: "{carrito.estado}".',
            )
        carrito.estado = 'procesado'
        carrito.save(update_fields=['estado'])
        return carrito
