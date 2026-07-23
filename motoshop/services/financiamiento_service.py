"""Lógica de negocio de financiamientos."""

from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from motoshop.models import Financiamiento
from motoshop.services.exceptions import BusinessError
from motoshop.services.transitions import FINANCIAMIENTO_TRANSICIONES, validar_transicion


class FinanciamientoService:
    @staticmethod
    def _calcular_cuota(monto, tasa, plazo_meses):
        if plazo_meses <= 0:
            raise BusinessError('El plazo debe ser mayor a cero.', field='plazo_meses')
        tasa_m = Decimal(str(tasa)) / Decimal('100') / Decimal('12')
        monto = Decimal(str(monto))
        if tasa_m == 0:
            cuota = monto / plazo_meses
        else:
            factor = (1 + tasa_m) ** plazo_meses
            cuota = monto * tasa_m * factor / (factor - 1)
        return cuota.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @classmethod
    @transaction.atomic
    def crear(cls, venta, entidad_financiera, monto_financiado, tasa_interes, plazo_meses,
              entrada=Decimal('0'), estado='activo'):
        if Financiamiento.objects.filter(id_venta=venta).exists():
            raise BusinessError(
                'Esta venta ya tiene un financiamiento registrado.',
                field='id_venta',
            )

        monto_financiado = Decimal(str(monto_financiado))
        entrada = Decimal(str(entrada or 0))
        total_venta = Decimal(str(venta.total_venta))

        if monto_financiado <= 0:
            raise BusinessError('El monto financiado debe ser mayor a cero.', field='monto_financiado')
        if plazo_meses <= 0:
            raise BusinessError('El plazo debe ser mayor a cero.', field='plazo_meses')
        if tasa_interes < 0:
            raise BusinessError('La tasa de interés no puede ser negativa.', field='tasa_interes')

        esperado = total_venta - entrada
        if abs(monto_financiado - esperado) > Decimal('0.01'):
            raise BusinessError(
                f'El monto financiado ({monto_financiado}) debe coincidir con '
                f'total venta ({total_venta}) menos entrada ({entrada}).',
                field='monto_financiado',
            )

        cuota = cls._calcular_cuota(monto_financiado, tasa_interes, plazo_meses)
        saldo = monto_financiado

        return Financiamiento.objects.create(
            id_venta=venta,
            entidad_financiera=entidad_financiera,
            monto_financiado=monto_financiado,
            tasa_interes=tasa_interes,
            plazo_meses=plazo_meses,
            cuota_mensual=cuota,
            entrada=entrada,
            saldo_pendiente=saldo,
            estado=estado,
        )

    @classmethod
    @transaction.atomic
    def registrar_abono(cls, financiamiento, monto):
        monto = Decimal(str(monto))
        if monto <= 0:
            raise BusinessError('El abono debe ser mayor a cero.')
        if financiamiento.estado == 'pagado':
            raise BusinessError('El financiamiento ya está pagado.')
        if monto > financiamiento.saldo_pendiente:
            raise BusinessError(
                f'El abono ({monto}) supera el saldo pendiente '
                f'({financiamiento.saldo_pendiente}).',
            )

        financiamiento.saldo_pendiente -= monto
        if financiamiento.saldo_pendiente <= 0:
            financiamiento.saldo_pendiente = Decimal('0')
            financiamiento.estado = 'pagado'
        financiamiento.save(update_fields=['saldo_pendiente', 'estado'])
        return financiamiento

    @classmethod
    def cambiar_estado(cls, financiamiento, nuevo_estado):
        validar_transicion(
            financiamiento.estado, nuevo_estado, FINANCIAMIENTO_TRANSICIONES, 'financiamiento',
        )
        financiamiento.estado = nuevo_estado
        financiamiento.save(update_fields=['estado'])
        return financiamiento
