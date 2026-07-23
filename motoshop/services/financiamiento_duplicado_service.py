"""
Análisis y resolución segura de financiamientos duplicados por venta.

Nota: cancelar un financiamiento duplicado NO basta para la restricción unique en
id_venta; los duplicados deben respaldarse (JSON) y eliminarse de la tabla activa,
o archivarse en otra tabla, tras confirmación explícita.
"""

from decimal import Decimal

from django.apps import apps
from django.db import transaction
from django.db.models import Sum

from motoshop.utils.financiamiento_audit import escribir_auditoria, respaldar_financiamiento


class ResolucionAbortada(Exception):
    pass


class ConfirmacionInvalida(Exception):
    pass


def _campo_disponible(model, nombre):
    try:
        model._meta.get_field(nombre)
        return True
    except Exception:
        return False


def _decimal(val):
    if val is None:
        return None
    return Decimal(str(val))


def _serializar_cliente(venta):
    cliente = venta.id_usuario_cliente
    return {
        'id': cliente.id,
        'username': cliente.username,
        'email': cliente.email,
    }


def _pagos_de_venta(Pago, venta_id, id_financiamiento=None):
    """Pagos de la venta; asociación a financiamiento solo si el campo existe en BD."""
    qs = Pago.objects.filter(id_venta_id=venta_id)
    tiene_fk_fin = _campo_disponible(Pago, 'id_financiamiento')
    resultado = []
    for p in qs:
        item = {
            'id_pago': p.id_pago,
            'monto': str(p.monto),
            'estado': p.estado,
            'tipo_pago': getattr(p, 'tipo_pago', None),
            'metodo_pago': p.metodo_pago,
            'fecha_pago': p.fecha_pago.isoformat() if p.fecha_pago else None,
        }
        if tiene_fk_fin:
            item['id_financiamiento'] = getattr(p, 'id_financiamiento_id', None)
            item['asignacion_concluyente'] = p.id_financiamiento_id == id_financiamiento
        else:
            item['id_financiamiento'] = None
            item['asignacion_concluyente'] = False
            item['nota'] = (
                'Pago.id_financiamiento no disponible (pre-migración 0005). '
                'Asignación inferida solo por venta, no concluyente.'
            )
        resultado.append(item)
    return resultado, tiene_fk_fin


def _total_pagado_venta(Pago, venta_id):
    total = (
        Pago.objects.filter(id_venta_id=venta_id, estado='completado')
        .aggregate(s=Sum('monto'))['s']
    )
    return _decimal(total or 0)


def _pagos_ligados_financiamiento(pagos, fin_id, tiene_fk):
    if tiene_fk:
        return [p for p in pagos if p.get('id_financiamiento') == fin_id]
    return []


def _completitud_score(f):
    campos = [
        f.entidad_financiera,
        f.monto_financiado,
        f.tasa_interes,
        f.plazo_meses,
        f.cuota_mensual,
    ]
    return sum(1 for c in campos if c is not None and str(c).strip() != '')


def _coherencia_venta(f, venta):
    advertencias = []
    total = _decimal(venta.total_venta or 0)
    entrada = _decimal(getattr(f, 'entrada', None) or 0)
    monto = _decimal(f.monto_financiado or 0)
    saldo_raw = getattr(f, 'saldo_pendiente', None)
    saldo = _decimal(saldo_raw) if saldo_raw is not None else None

    total_financiado = entrada + monto
    if total_financiado > total:
        advertencias.append(
            f'Financiamiento {f.id_financiamiento}: '
            f'entrada + monto_financiado supera total_venta '
            f'({total_financiado} > {total})'
        )
    if saldo is not None and saldo < 0:
        advertencias.append(
            f'Financiamiento {f.id_financiamiento}: saldo_pendiente negativo: {saldo}'
        )
    return advertencias


def validar_venta_financiera(venta, financiamientos, pagos_venta):
    advertencias = []
    total = _decimal(venta.total_venta)
    pagado = sum(
        _decimal(p['monto']) for p in pagos_venta if p['estado'] == 'completado'
    )
    if pagado > total:
        advertencias.append(f'total_pagado ({pagado}) supera total_venta ({total})')

    activos = [f for f in financiamientos if f.estado == 'activo']
    if len(activos) > 1:
        advertencias.append(f'más de un financiamiento activo: {[f.id_financiamiento for f in activos]}')

    for f in financiamientos:
        advertencias.extend(
            f'Fin #{f.id_financiamiento}: {a}' for a in _coherencia_venta(f, venta)
        )
    return advertencias


def sugerir_conservar(financiamientos, venta, pagos_venta, tiene_fk_fin):
    """Orden: pagos > activo > coherencia > id menor > completitud."""
    def score(f):
        pagos_fin = _pagos_ligados_financiamiento(pagos_venta, f.id_financiamiento, tiene_fk_fin)
        pagos_count = len(pagos_fin) if tiene_fk_fin else 0
        pagos_total = sum(_decimal(p['monto']) for p in pagos_fin)
        coherencia_ok = len(_coherencia_venta(f, venta)) == 0
        activo = 1 if f.estado == 'activo' else 0
        return (
            pagos_count,
            float(pagos_total),
            activo,
            1 if coherencia_ok else 0,
            -f.id_financiamiento,
            _completitud_score(f),
        )

    ordenados = sorted(financiamientos, key=score, reverse=True)
    elegido = ordenados[0]
    pagos_fin = _pagos_ligados_financiamiento(pagos_venta, elegido.id_financiamiento, tiene_fk_fin)
    razones = []
    if tiene_fk_fin and pagos_fin:
        razones.append(f'tiene {len(pagos_fin)} pago(s) asociado(s) por id_financiamiento')
    elif not tiene_fk_fin:
        razones.append(
            'sin id_financiamiento en pagos (pre-0005); criterio basado en estado y coherencia'
        )
    if elegido.estado == 'activo':
        razones.append('estado activo')
    if not _coherencia_venta(elegido, venta):
        razones.append('coherencia parcial respecto a la venta')
    else:
        razones.append('coherencia respecto a la venta')
    razones.append(f'id más antiguo entre empates (#{elegido.id_financiamiento})')

    return elegido, '; '.join(razones)


def analizar_financiamiento(f, venta, Pago):
    pagos_venta, tiene_fk = _pagos_de_venta(Pago, venta.id_venta, f.id_financiamiento)
    pagos_fin = _pagos_ligados_financiamiento(pagos_venta, f.id_financiamiento, tiene_fk)
    total_pagado_fin = sum(_decimal(p['monto']) for p in pagos_fin if p['estado'] == 'completado')

    return {
        'id_financiamiento': f.id_financiamiento,
        'monto_financiado': str(f.monto_financiado),
        'entrada': str(getattr(f, 'entrada', 'N/A (pre-migración 0005)')),
        'saldo_pendiente': str(getattr(f, 'saldo_pendiente', 'N/A (pre-migración 0005)')),
        'tasa_interes': str(f.tasa_interes),
        'plazo_meses': f.plazo_meses,
        'cuota_mensual': str(f.cuota_mensual),
        'estado': f.estado,
        'entidad_financiera': f.entidad_financiera,
        'fecha_creacion': None,
        'nota_fecha': 'El modelo Financiamiento no tiene fecha_creacion; use id_financiamiento como proxy.',
        'cantidad_pagos_relacionados': len(pagos_fin),
        'total_pagado_relacionado': str(total_pagado_fin),
        'pagos_asignacion_concluyente': tiene_fk,
        'advertencias': _coherencia_venta(f, venta),
    }


def detectar_duplicados():
    Financiamiento = apps.get_model('motoshop', 'Financiamiento')
    Venta = apps.get_model('motoshop', 'Venta')
    Pago = apps.get_model('motoshop', 'Pago')

    por_venta = {}
    for f in (
        Financiamiento.objects
        .select_related('id_venta__id_usuario_cliente')
        .order_by('id_venta_id', 'id_financiamiento')
    ):
        por_venta.setdefault(f.id_venta_id, []).append(f)

    duplicadas = []
    total_ventas = Venta.objects.count()
    total_fin = 0
    total_pagos = 0

    for id_venta, fins in por_venta.items():
        if len(fins) <= 1:
            continue
        venta = fins[0].id_venta
        pagos_venta, tiene_fk = _pagos_de_venta(Pago, id_venta)
        sugerido, justificacion = sugerir_conservar(fins, venta, pagos_venta, tiene_fk)
        advertencias = validar_venta_financiera(venta, fins, pagos_venta)

        item = {
            'id_venta': id_venta,
            'total_venta': str(venta.total_venta),
            'estado_venta': venta.estado,
            'cliente': _serializar_cliente(venta),
            'cantidad_financiamientos': len(fins),
            'financiamientos': [analizar_financiamiento(f, venta, Pago) for f in fins],
            'pagos': pagos_venta,
            'pagos_nota_global': (
                None if tiene_fk else
                'Pago.id_financiamiento no disponible: pagos listados por venta; '
                'asignación a financiamiento no concluyente.'
            ),
            'sugerido_conservar_id': sugerido.id_financiamiento,
            'sugerido_justificacion': justificacion,
            'advertencias': advertencias,
            'acciones_sugeridas': [
                'Conservar un financiamiento y archivar/eliminar duplicados (unique id_venta).',
                'Cancelar duplicados NO basta: todos comparten id_venta y bloquean UniqueConstraint.',
                f'Sugerido conservar #{sugerido.id_financiamiento}: {justificacion}',
            ],
        }
        duplicadas.append(item)
        total_fin += len(fins)
        total_pagos += len(pagos_venta)

    resumen = {
        'ventas_analizadas': total_ventas,
        'ventas_con_duplicados': len(duplicadas),
        'financiamientos_involucrados': total_fin,
        'pagos_relacionados': total_pagos,
        'registros_requieren_intervencion': len(duplicadas),
    }
    return duplicadas, resumen


def exportar_reporte(ruta):
    import json
    from pathlib import Path

    duplicadas, resumen = detectar_duplicados()
    payload = {'resumen': resumen, 'ventas_duplicadas': duplicadas}
    path = Path(ruta)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)
    return path, payload


@transaction.atomic
def cancelar_duplicados(venta_id, conservar_id, usuario='', audit_path=None):
    """Cancela duplicados; requiere paso posterior de respaldo+eliminación para unique."""
    Financiamiento = apps.get_model('motoshop', 'Financiamiento')
    fins = list(
        Financiamiento.objects.select_for_update().filter(id_venta_id=venta_id)
    )
    if len(fins) <= 1:
        raise ResolucionAbortada('La venta no tiene duplicados.')

    conservar = next((f for f in fins if f.id_financiamiento == conservar_id), None)
    if not conservar:
        raise ConfirmacionInvalida(f'No existe financiamiento #{conservar_id} en venta #{venta_id}.')

    entradas_audit = []
    modificados = []
    for f in fins:
        if f.id_financiamiento == conservar_id:
            continue
        anterior = respaldar_financiamiento(f, venta_id, 'pre-cancelacion')
        f.estado = 'cancelado'
        update_fields = ['estado']
        if _campo_disponible(Financiamiento, 'saldo_pendiente'):
            f.saldo_pendiente = Decimal('0')
            update_fields.append('saldo_pendiente')
        f.save(update_fields=update_fields)
        modificados.append({
            'accion': 'cancelado',
            'id_financiamiento': f.id_financiamiento,
            'valores_anteriores': anterior,
            'valores_nuevos': respaldar_financiamiento(f, venta_id, 'post-cancelacion'),
            'motivo': 'Cancelado durante resolución de duplicados previa a migración 0007.',
            'observacion': (
                'Cancelado durante resolución de duplicados previa a migración 0005/0007. '
                'Aún vinculado a id_venta; requiere respaldo y eliminación para unique.'
            ),
        })

    entradas_audit.append({
        'venta_afectada': venta_id,
        'financiamiento_conservado': conservar_id,
        'financiamientos_modificados': modificados,
        'usuario_ejecutor': usuario,
        'motivo': 'cancelar_duplicados',
    })
    if audit_path:
        escribir_auditoria(audit_path, entradas_audit, usuario)
    return entradas_audit


@transaction.atomic
def respaldar_y_eliminar_duplicados(venta_id, conservar_id, usuario='', audit_path=None):
    """Respaldo JSON + eliminación de duplicados cancelados (confirmación previa obligatoria)."""
    Financiamiento = apps.get_model('motoshop', 'Financiamiento')
    fins = list(
        Financiamiento.objects.select_for_update().filter(id_venta_id=venta_id)
    )
    conservar = next((f for f in fins if f.id_financiamiento == conservar_id), None)
    if not conservar:
        raise ConfirmacionInvalida(f'No existe financiamiento #{conservar_id}.')

    eliminados = []
    for f in fins:
        if f.id_financiamiento == conservar_id:
            continue
        snapshot = respaldar_financiamiento(f, venta_id, 'pre-eliminacion')
        fin_id = f.id_financiamiento
        f.delete()
        eliminados.append({
            'accion': 'eliminado_tras_respaldo',
            'id_financiamiento': fin_id,
            'valores_anteriores': snapshot,
            'motivo': 'Eliminado tras respaldo para permitir UniqueConstraint id_venta.',
        })

    entrada = {
        'venta_afectada': venta_id,
        'financiamiento_conservado': conservar_id,
        'financiamientos_eliminados': eliminados,
        'usuario_ejecutor': usuario,
        'motivo': 'respaldar_y_eliminar',
    }
    if audit_path:
        escribir_auditoria(audit_path, [entrada], usuario)
    return entrada


def venta_tiene_duplicados(venta_id):
    Financiamiento = apps.get_model('motoshop', 'Financiamiento')
    return Financiamiento.objects.filter(id_venta_id=venta_id).count() > 1


def hay_duplicados_globales():
    _, resumen = detectar_duplicados()
    return resumen['ventas_con_duplicados'] > 0
