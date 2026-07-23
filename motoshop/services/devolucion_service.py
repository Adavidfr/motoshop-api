"""Lógica de negocio de devoluciones.

Devolución total (sin líneas de detalle):
  - Reintegra el carrito completo de la venta al inventario.
  - monto_devolucion = reembolso monetario solicitado (puede ser 0).
  - monto_reembolso <= total_pagado y <= venta.total_venta.
  - Sin pagos completados: devolución física permitida con reembolso 0.
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from motoshop.models import Devolucion
from motoshop.services.constants import DEVOLUCION_PLAZO_DIAS
from motoshop.services.exceptions import BusinessError
from motoshop.services.inventario_service import InventarioService
from motoshop.services.notificacion_service import NotificacionService
from motoshop.services.pago_service import PagoService
from motoshop.services.transitions import DEVOLUCION_TRANSICIONES, validar_transicion
from motoshop.services.venta_service import VentaService


class DevolucionService:
    ESTADOS_ABIERTOS = {'solicitada', 'aprobada'}

    @classmethod
    def _monto_productos_devueltos(cls, venta):
        """Devolución total: el tope monetario es el total comercial de la venta."""
        return Decimal(str(venta.total_venta))

    @classmethod
    def _calcular_reembolso_permitido(cls, venta, monto_solicitado):
        pagado = VentaService.total_pagado(venta)
        tope_productos = cls._monto_productos_devueltos(venta)
        monto = Decimal(str(monto_solicitado))
        if monto <= 0:
            return Decimal('0')
        return min(monto, pagado, tope_productos)

    @classmethod
    def _validar_plazo(cls, venta):
        limite = venta.fecha_venta + timezone.timedelta(days=DEVOLUCION_PLAZO_DIAS)
        if timezone.now() > limite:
            raise BusinessError(
                f'El plazo de devolución ({DEVOLUCION_PLAZO_DIAS} días) ha expirado.',
            )

    @classmethod
    @transaction.atomic
    def solicitar(cls, venta, usuario, motivo, monto_devolucion):
        if venta.id_usuario_cliente_id != usuario.id:
            raise BusinessError('Solo puedes solicitar devoluciones sobre tus propias ventas.')
        if not motivo or not motivo.strip():
            raise BusinessError('El motivo es obligatorio.', field='motivo')

        monto = Decimal(str(monto_devolucion))
        if monto < 0:
            raise BusinessError('El monto no puede ser negativo.', field='monto_devolucion')

        cls._validar_plazo(venta)
        pagado = VentaService.total_pagado(venta)
        tope_productos = cls._monto_productos_devueltos(venta)

        if monto > 0 and pagado <= 0:
            raise BusinessError(
                'No hay pagos completados; el reembolso solicitado debe ser 0.',
                field='monto_devolucion',
            )
        if monto > pagado:
            raise BusinessError(
                f'El reembolso solicitado ({monto}) supera lo pagado ({pagado}).',
                field='monto_devolucion',
            )
        if monto > tope_productos:
            raise BusinessError(
                f'El reembolso solicitado ({monto}) supera el valor de la venta ({tope_productos}).',
                field='monto_devolucion',
            )

        if Devolucion.objects.filter(
            id_venta=venta,
            estado__in=cls.ESTADOS_ABIERTOS,
        ).exists():
            raise BusinessError('Ya existe una devolución pendiente para esta venta.')

        return Devolucion.objects.create(
            id_venta=venta,
            motivo=motivo,
            monto_devolucion=monto,
            estado='solicitada',
        )

    @classmethod
    @transaction.atomic
    def cambiar_estado(cls, devolucion, nuevo_estado, actor):
        devolucion = (
            Devolucion.objects
            .select_for_update(of=('self',))
            .select_related('id_venta', 'id_venta__id_pedido__id_carrito')
            .get(pk=devolucion.pk)
        )
        validar_transicion(devolucion.estado, nuevo_estado, DEVOLUCION_TRANSICIONES, 'devolución')

        if nuevo_estado == 'aprobada':
            cls._aprobar(devolucion, actor)
        elif nuevo_estado == 'rechazada':
            devolucion.estado = 'rechazada'
            devolucion.fecha_resolucion = timezone.now()
            devolucion.save(update_fields=['estado', 'fecha_resolucion'])
            NotificacionService.devolucion_resuelta(devolucion, aprobada=False)
        elif nuevo_estado == 'completada':
            if devolucion.estado != 'aprobada':
                raise BusinessError('Solo se puede completar una devolución aprobada.')
            devolucion.estado = 'completada'
            devolucion.fecha_resolucion = timezone.now()
            devolucion.save(update_fields=['estado', 'fecha_resolucion'])
        else:
            devolucion.estado = nuevo_estado
            devolucion.save(update_fields=['estado'])

        return devolucion

    @classmethod
    def _aprobar(cls, devolucion, actor):
        if devolucion.estado != 'solicitada':
            raise BusinessError('Solo se pueden aprobar devoluciones en estado "solicitada".')
        if devolucion.stock_reintegrado:
            raise BusinessError('El stock de esta devolución ya fue reintegrado.')

        venta = devolucion.id_venta
        carrito = venta.id_pedido.id_carrito if venta.id_pedido_id else None

        if carrito and carrito.items.exists():
            InventarioService.reintegrar_por_carrito(
                carrito,
                actor,
                referencia=f'Devolución #{devolucion.id_devolucion}',
            )
            devolucion.stock_reintegrado = True

        reembolso = cls._calcular_reembolso_permitido(venta, devolucion.monto_devolucion)
        if reembolso > 0:
            PagoService.registrar_reembolso(
                venta,
                reembolso,
                actor,
                referencia=f'Devolución #{devolucion.id_devolucion}',
            )
            devolucion.monto_reembolso_aplicado = reembolso
        else:
            devolucion.monto_reembolso_aplicado = Decimal('0')

        devolucion.estado = 'aprobada'
        devolucion.fecha_resolucion = timezone.now()
        devolucion.save(update_fields=[
            'estado', 'fecha_resolucion', 'stock_reintegrado', 'monto_reembolso_aplicado',
        ])
        NotificacionService.devolucion_resuelta(devolucion, aprobada=True)
