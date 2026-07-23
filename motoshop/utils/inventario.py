from django.db.models import Sum
from rest_framework import serializers

from motoshop.models import ItemCarrito
from motoshop.models.moto import Moto
from motoshop.models.repuesto import Repuesto


class StockInsuficienteError(serializers.ValidationError):
    pass


def resolver_producto(id_moto=None, id_repuesto=None):
    """Devuelve (precio, stock, etiqueta) para una moto o repuesto."""
    if id_moto:
        try:
            moto = Moto.objects.get(pk=id_moto)
        except Moto.DoesNotExist:
            raise serializers.ValidationError({'id_moto': 'La moto no existe.'})
        if moto.estado != 'disponible':
            raise serializers.ValidationError(
                {'id_moto': f'La moto no está disponible (estado: "{moto.estado}").'}
            )
        return moto.precio, moto.stock, f'{moto.modelo}'

    try:
        repuesto = Repuesto.objects.get(pk=id_repuesto)
    except Repuesto.DoesNotExist:
        raise serializers.ValidationError({'id_repuesto': 'El repuesto no existe.'})
    if repuesto.stock <= 0:
        raise serializers.ValidationError(
            {'id_repuesto': 'El repuesto no tiene stock disponible.'}
        )
    return repuesto.precio_venta, repuesto.stock, repuesto.nombre


def cantidad_en_carrito(carrito, id_moto=None, id_repuesto=None, exclude_item_id=None):
    filtro = {'id_carrito': carrito}
    if id_moto:
        filtro['id_moto'] = id_moto
    else:
        filtro['id_repuesto'] = id_repuesto

    qs = ItemCarrito.objects.filter(**filtro)
    if exclude_item_id:
        qs = qs.exclude(id_item=exclude_item_id)
    return qs.aggregate(total=Sum('cantidad'))['total'] or 0


def validar_stock_solicitado(
    id_moto,
    id_repuesto,
    cantidad_requerida,
    carrito=None,
    exclude_item_id=None,
):
    """Valida que la cantidad requerida no supere el stock disponible."""
    _, stock, etiqueta = resolver_producto(id_moto, id_repuesto)

    if exclude_item_id is not None:
        total_solicitado = cantidad_requerida
    elif carrito is not None:
        total_solicitado = cantidad_en_carrito(
            carrito,
            id_moto=id_moto,
            id_repuesto=id_repuesto,
        ) + cantidad_requerida
    else:
        total_solicitado = cantidad_requerida

    if total_solicitado > stock:
        raise serializers.ValidationError(
            f'Stock insuficiente para {etiqueta}. '
            f'Disponible: {stock}, solicitado: {total_solicitado}.'
        )


def validar_stock_carrito(carrito):
    """Revalida stock de todos los ítems de un carrito."""
    for item in carrito.items.all():
        validar_stock_solicitado(
            item.id_moto,
            item.id_repuesto,
            item.cantidad,
        )
