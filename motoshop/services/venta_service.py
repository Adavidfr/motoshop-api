"""Lógica de negocio de ventas."""

from decimal import Decimal

from django.db import transaction

from motoshop.models import Venta
from motoshop.services.exceptions import BusinessError
from motoshop.services.historial_venta_service import HistorialVentaService
from motoshop.services.inventario_service import InventarioService
from motoshop.services.notificacion_service import NotificacionService


class VentaService:
    @staticmethod
    def _calcular_total_desde_pedido(pedido):
        if pedido.total and pedido.total > 0:
            return pedido.total
        if pedido.id_carrito:
            return Decimal(str(pedido.id_carrito.calcular_total()))
        raise BusinessError('No se pudo calcular el total del pedido.')

    @classmethod
    @transaction.atomic
    def crear_venta_desde_pedido(cls, pedido_id, admin_user, estado='pendiente'):
        from motoshop.models import Pedido

        try:
            pedido = (
                Pedido.objects
                .select_for_update(of=('self',))
                .select_related('id_carrito', 'id_usuario_cliente')
                .get(pk=pedido_id)
            )
        except Pedido.DoesNotExist:
            raise BusinessError('El pedido no existe.', field='id_pedido')

        if pedido.estado != 'confirmed':
            raise BusinessError(
                f'El pedido debe estar confirmado. Estado actual: "{pedido.estado}".',
                field='id_pedido',
            )

        if hasattr(pedido, 'venta') and pedido.venta is not None:
            raise BusinessError(
                'Ya existe una venta para este pedido.',
                field='id_pedido',
            )

        if Venta.objects.filter(id_pedido=pedido).exists():
            raise BusinessError(
                'Ya existe una venta para este pedido.',
                field='id_pedido',
            )

        if not pedido.id_carrito or not pedido.id_carrito.items.exists():
            raise BusinessError('El pedido no tiene ítems para procesar.')

        total_venta = cls._calcular_total_desde_pedido(pedido)

        InventarioService.disminuir_por_carrito(
            pedido.id_carrito,
            admin_user,
            referencia=f'Venta desde pedido #{pedido.id_pedido}',
        )

        venta = Venta.objects.create(
            id_pedido=pedido,
            id_usuario_cliente=pedido.id_usuario_cliente,
            id_usuario_vendedor=admin_user,
            total_venta=total_venta,
            estado=estado,
        )

        # El pedido permanece en confirmed; shipped requiere acción explícita del admin.

        HistorialVentaService.registrar(
            venta,
            estado_anterior='',
            estado_nuevo=estado,
            actor=admin_user,
            observacion='Venta creada desde pedido confirmado.',
        )
        NotificacionService.venta_creada(venta)
        return venta

    @classmethod
    @transaction.atomic
    def cambiar_estado(cls, venta, nuevo_estado, actor=None, observacion=''):
        return HistorialVentaService.cambiar_estado_venta(
            venta, nuevo_estado, actor, observacion,
        )

    @staticmethod
    def total_pagado(venta):
        from django.db.models import Sum
        from motoshop.models import Pago

        total = (
            Pago.objects
            .filter(id_venta=venta, estado='completado')
            .aggregate(s=Sum('monto'))['s']
        )
        return Decimal(str(total or 0))

    @staticmethod
    def saldo_pendiente(venta):
        return venta.total_venta - VentaService.total_pagado(venta)

    @classmethod
    def construir_resumen(cls, venta):
        from motoshop.serializers.pago import PagoSerializer
        from motoshop.serializers.factura import FacturaSerializer
        from motoshop.serializers.financiamiento import FinanciamientoSerializer
        from motoshop.serializers.garantia import GarantiaSerializer
        from motoshop.serializers.seguro import SeguroSerializer
        from motoshop.serializers.documento_venta import DocumentoVentaSerializer
        from motoshop.serializers.pedido import PedidoSerializer

        financiamiento = venta.financiamientos.first()
        from motoshop.models import Factura
        facturas = Factura.objects.filter(id_pago__id_venta=venta).select_related('id_pago')
        total_pagado = cls.total_pagado(venta)

        return {
            'id': venta.id_venta,
            'estado': venta.estado,
            'total_venta': float(venta.total_venta),
            'total_pagado': float(total_pagado),
            'saldo_pendiente': float(venta.total_venta - total_pagado),
            'procesado_por': {
                'id': venta.id_usuario_vendedor_id,
                'username': venta.id_usuario_vendedor.username,
            } if venta.id_usuario_vendedor_id else None,
            'pedido': PedidoSerializer(venta.id_pedido).data if venta.id_pedido_id else None,
            'pagos': PagoSerializer(venta.pagos.all(), many=True).data,
            'financiamiento': (
                FinanciamientoSerializer(financiamiento).data if financiamiento else None
            ),
            'facturas': FacturaSerializer(facturas, many=True).data,
            'garantias': GarantiaSerializer(venta.garantias.all(), many=True).data,
            'seguros': SeguroSerializer(venta.seguros.all(), many=True).data,
            'documentos': DocumentoVentaSerializer(venta.documentos.all(), many=True).data,
        }
