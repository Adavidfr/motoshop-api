"""Lógica de negocio de pedidos."""

from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError as DRFValidationError

from motoshop.models import Pedido
from motoshop.services.carrito_service import CarritoService
from motoshop.services.exceptions import BusinessError
from motoshop.services.inventario_service import InventarioService
from motoshop.services.notificacion_service import NotificacionService
from motoshop.services.transitions import PEDIDO_TRANSICIONES, validar_transicion


def _validation_error_a_negocio(exc):
    detail = exc.detail
    if isinstance(detail, dict):
        val = next(iter(detail.values()))
        detail = val[0] if isinstance(val, list) else val
    elif isinstance(detail, list):
        detail = detail[0]
    raise BusinessError(str(detail))


class PedidoService:
    @classmethod
    @transaction.atomic
    def crear_desde_carrito(cls, usuario, carrito):
        if carrito.id_usuario_cliente_id != usuario.id:
            raise BusinessError('El carrito no pertenece al usuario autenticado.', field='id_carrito')
        if carrito.estado != 'activo':
            raise BusinessError(
                f'Solo se puede crear un pedido desde un carrito activo. '
                f'Estado actual: "{carrito.estado}".',
                field='id_carrito',
            )
        if not carrito.items.exists():
            raise BusinessError('No se puede crear un pedido desde un carrito vacío.', field='id_carrito')
        if Pedido.objects.filter(id_carrito=carrito).exists():
            raise BusinessError(
                'Ya existe un pedido para este carrito.',
                field='id_carrito',
            )

        try:
            InventarioService.validar_stock_carrito(carrito)
        except DRFValidationError as exc:
            _validation_error_a_negocio(exc)
        total = Decimal(str(carrito.calcular_total()))

        pedido = Pedido.objects.create(
            id_usuario_cliente=usuario,
            id_carrito=carrito,
            total=total,
            estado='pending',
        )
        CarritoService.marcar_procesado(carrito)
        return pedido

    @classmethod
    @transaction.atomic
    def confirmar(cls, pedido, usuario):
        if pedido.id_usuario_cliente_id != usuario.id:
            raise BusinessError('No tienes permiso para confirmar este pedido.')
        if pedido.estado != 'pending':
            raise BusinessError('Solo se pueden confirmar pedidos en estado "pending".')
        if pedido.id_carrito and not pedido.id_carrito.items.exists():
            raise BusinessError('No se puede confirmar un pedido con el carrito vacío.')
        if pedido.id_carrito:
            try:
                InventarioService.validar_stock_carrito(pedido.id_carrito)
            except DRFValidationError as exc:
                _validation_error_a_negocio(exc)

        pedido.estado = 'confirmed'
        pedido.save(update_fields=['estado'])
        NotificacionService.pedido_confirmado(pedido)
        return pedido

    @classmethod
    @transaction.atomic
    def cambiar_estado(cls, pedido, nuevo_estado, actor=None):
        validar_transicion(pedido.estado, nuevo_estado, PEDIDO_TRANSICIONES, 'pedido')
        pedido.estado = nuevo_estado
        pedido.save(update_fields=['estado'])
        return pedido
