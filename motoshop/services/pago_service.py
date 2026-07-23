"""Lógica de negocio de pagos."""

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from motoshop.models import Pago
from motoshop.services.exceptions import BusinessError
from motoshop.services.financiamiento_service import FinanciamientoService
from motoshop.services.historial_venta_service import HistorialVentaService
from motoshop.services.notificacion_service import NotificacionService
from motoshop.services.venta_service import VentaService


class PagoService:
    TIPOS_FINANCIAMIENTO = {'entrada', 'cuota', 'abono'}

    @staticmethod
    def _total_pagado_venta(venta, excluir_pago=None):
        qs = Pago.objects.filter(id_venta=venta, estado='completado')
        if excluir_pago:
            qs = qs.exclude(pk=excluir_pago.pk)
        total = qs.aggregate(s=Sum('monto'))['s']
        return Decimal(str(total or 0))

    @classmethod
    @transaction.atomic
    def registrar_pago(
        cls,
        venta,
        monto,
        metodo_pago,
        procesado_por,
        tipo_pago='contado',
        id_financiamiento=None,
        estado='completado',
        referencia='',
        comprobante=None,
    ):
        """Registra un pago. `id_financiamiento` debe ser int | None (PK), no instancia."""
        monto = Decimal(str(monto))
        if monto <= 0:
            raise BusinessError('El monto del pago debe ser mayor a cero.', field='monto')

        if estado == 'completado':
            pagado = cls._total_pagado_venta(venta)
            saldo = venta.total_venta - pagado
            if monto > saldo:
                raise BusinessError(
                    f'El pago ({monto}) supera el saldo pendiente de la venta ({saldo}).',
                    field='monto',
                )

        financiamiento = None
        if id_financiamiento:
            financiamiento = venta.financiamientos.filter(pk=id_financiamiento).first()
            if not financiamiento:
                raise BusinessError(
                    'El financiamiento no pertenece a esta venta.',
                    field='id_financiamiento',
                )

        pago = Pago.objects.create(
            id_venta=venta,
            monto=monto,
            metodo_pago=metodo_pago,
            tipo_pago=tipo_pago,
            id_financiamiento=financiamiento,
            procesado_por=procesado_por,
            estado=estado,
            referencia=referencia,
            comprobante=comprobante,
        )

        if estado == 'completado' and financiamiento and tipo_pago in cls.TIPOS_FINANCIAMIENTO:
            FinanciamientoService.registrar_abono(financiamiento, monto)
            if financiamiento.estado == 'pagado':
                NotificacionService.financiamiento_pagado(financiamiento)

        if estado == 'completado':
            NotificacionService.pago_registrado(pago)
            if VentaService.saldo_pendiente(venta) <= 0 and venta.estado == 'pendiente':
                HistorialVentaService.cambiar_estado_venta(
                    venta, 'completada', procesado_por,
                    observacion='Venta completada por pago total.',
                )

        return pago

    @classmethod
    @transaction.atomic
    def registrar_reembolso(cls, venta, monto, procesado_por, metodo_pago='otro', referencia=''):
        monto = Decimal(str(monto))
        pagado = cls._total_pagado_venta(venta)
        if monto > pagado:
            raise BusinessError(
                f'El reembolso ({monto}) supera el total pagado ({pagado}).',
                field='monto',
            )
        return cls.registrar_pago(
            venta=venta,
            monto=monto,
            metodo_pago=metodo_pago,
            procesado_por=procesado_por,
            tipo_pago='reembolso',
            estado='reembolsado',
            referencia=referencia,
        )
