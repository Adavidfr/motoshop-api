"""Matrices de transiciones de estado válidas por entidad."""

from motoshop.services.exceptions import BusinessError

# CarritoCompras: activo → procesado | abandonado (procesado es terminal para ítems)
CARRITO_TERMINAL = {'procesado', 'abandonado'}

# Pedido
PEDIDO_TRANSICIONES = {
    'pending':   {'confirmed', 'cancelled'},
    'confirmed': {'shipped', 'cancelled'},
    'shipped':   {'delivered'},
    'delivered': set(),
    'cancelled': set(),
}

# Venta
VENTA_TRANSICIONES = {
    'pendiente':  {'completada', 'anulada'},
    'completada': set(),
    'anulada':    set(),
}

# Financiamiento
FINANCIAMIENTO_TRANSICIONES = {
    'activo':    {'pagado', 'vencido', 'cancelado'},
    'pagado':    set(),
    'vencido':   {'pagado', 'cancelado'},
    'cancelado': set(),
}

# Garantía
GARANTIA_TRANSICIONES = {
    'activa':  {'vencida', 'anulada'},
    'vencida': set(),
    'anulada': set(),
}

# Seguro
SEGURO_TRANSICIONES = {
    'activo':    {'vencido', 'cancelado'},
    'vencido':   set(),
    'cancelado': set(),
}

# Compra (valores reales del modelo)
COMPRA_TRANSICIONES = {
    'Pendiente': {'Recibida', 'Cancelada'},
    'Recibida':  set(),
    'Cancelada': set(),
}

# Mantenimiento
MANTENIMIENTO_TRANSICIONES = {
    'Pendiente':   {'En proceso', 'Cancelado'},
    'En proceso':  {'Finalizado', 'Cancelado'},
    'Finalizado':  set(),
    'Cancelado':   set(),
}

# Devolución
DEVOLUCION_TRANSICIONES = {
    'solicitada': {'aprobada', 'rechazada'},
    'aprobada':   {'completada'},
    'rechazada':  set(),
    'completada': set(),
}


def validar_transicion(actual, nuevo, matriz, entidad='registro'):
    if actual == nuevo:
        return
    permitidos = matriz.get(actual, set())
    if nuevo not in permitidos:
        raise BusinessError(
            f'Transición inválida para {entidad}: "{actual}" → "{nuevo}". '
            f'Permitidas: {sorted(permitidos) or "ninguna"}.',
        )
