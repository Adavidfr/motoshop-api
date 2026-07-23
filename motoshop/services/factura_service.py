"""Lógica de negocio de facturas."""

import re

from django.db import transaction
from django.utils import timezone

from motoshop.models import Factura
from motoshop.services.exceptions import BusinessError
from motoshop.services.notificacion_service import NotificacionService
from motoshop.utils.facturacion import descomponer_total_con_iva

_NUMERO_FACTURA_PATTERN = re.compile(r'^FAC-(\d{4})-(\d{6})$')


class FacturaService:
    @staticmethod
    def _prefijo_anio(anio=None):
        year = anio if anio is not None else timezone.now().year
        return f'FAC-{year}-'

    @classmethod
    def _generar_numero_factura(cls, anio=None):
        """Genera FAC-{AÑO}-{SECUENCIAL} con secuencial de 6 dígitos por año."""
        year = anio if anio is not None else timezone.now().year
        prefix = cls._prefijo_anio(year)

        numeros = (
            Factura.objects
            .select_for_update()
            .filter(numero_factura__startswith=prefix)
            .values_list('numero_factura', flat=True)
        )

        max_seq = 0
        for numero in numeros:
            match = _NUMERO_FACTURA_PATTERN.match(numero)
            if match and int(match.group(1)) == year:
                max_seq = max(max_seq, int(match.group(2)))

        return f'{prefix}{max_seq + 1:06d}'

    @classmethod
    @transaction.atomic
    def emitir(cls, venta, numero_factura=None, procesado_por=None):
        if hasattr(venta, 'factura') and venta.factura is not None:
            raise BusinessError(
                'Esta venta ya tiene una factura emitida.',
                field='id_venta',
            )
        if Factura.objects.filter(id_venta=venta).exists():
            raise BusinessError('Esta venta ya tiene una factura emitida.', field='id_venta')

        if numero_factura is None:
            numero_factura = cls._generar_numero_factura()
        elif Factura.objects.filter(numero_factura=numero_factura).exists():
            raise BusinessError(
                f'El número de factura "{numero_factura}" ya existe.',
                field='numero_factura',
            )

        subtotal, iva, total = descomponer_total_con_iva(venta.total_venta)

        factura = Factura.objects.create(
            id_venta=venta,
            numero_factura=numero_factura,
            subtotal=subtotal,
            iva=iva,
            total=total,
        )
        NotificacionService.factura_emitida(factura)
        return factura
