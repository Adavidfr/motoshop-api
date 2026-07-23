"""
Utilidades de facturación.

Regla comercial adoptada:
  Venta.total_venta  = total final comercial (incluye IVA).
  Factura.subtotal   = base imponible  = total / (1 + tasa).
  Factura.iva        = impuesto       = total - subtotal.
  Factura.total      = subtotal + iva  = Venta.total_venta (sin sumar IVA dos veces).
"""

from decimal import Decimal

from django.conf import settings


def obtener_tasa_iva():
    """Devuelve MOTOSHOP_IVA_RATE como Decimal."""
    return Decimal(str(settings.MOTOSHOP_IVA_RATE))


def descomponer_total_con_iva(total_final):
    """
    Descompone un total final (con IVA incluido) en subtotal e impuesto.
    Usa Decimal en todo el cálculo.
    """
    total = Decimal(str(total_final))
    tasa = obtener_tasa_iva()
    if tasa < 0:
        raise ValueError('MOTOSHOP_IVA_RATE no puede ser negativa.')
    if tasa == 0:
        return total, Decimal('0.00'), total
    subtotal = (total / (1 + tasa)).quantize(Decimal('0.01'))
    impuestos = (total - subtotal).quantize(Decimal('0.01'))
    return subtotal, impuestos, total
