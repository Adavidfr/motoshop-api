"""Auditoría estructurada para resolución de financiamientos duplicados."""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.conf import settings


def _json_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f'No serializable: {type(obj)}')


def logs_dir():
    base = Path(getattr(settings, 'BASE_DIR', Path.cwd()))
    path = base / 'logs'
    path.mkdir(parents=True, exist_ok=True)
    return path


def nuevo_archivo_auditoria():
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    return logs_dir() / f'resolucion_financiamientos_{ts}.json'


def escribir_auditoria(ruta, entradas, usuario_ejecutor=''):
    payload = {
        'generado_en': datetime.now().isoformat(),
        'usuario_ejecutor': usuario_ejecutor,
        'entradas': entradas,
    }
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open('w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, default=_json_default)
    return ruta


def respaldar_financiamiento(financiamiento, venta_id, motivo):
    """Snapshot JSON de un financiamiento antes de modificar/eliminar."""
    return {
        'id_financiamiento': financiamiento.id_financiamiento,
        'id_venta': venta_id,
        'entidad_financiera': financiamiento.entidad_financiera,
        'monto_financiado': financiamiento.monto_financiado,
        'entrada': getattr(financiamiento, 'entrada', None),
        'saldo_pendiente': getattr(financiamiento, 'saldo_pendiente', None),
        'tasa_interes': financiamiento.tasa_interes,
        'plazo_meses': financiamiento.plazo_meses,
        'cuota_mensual': financiamiento.cuota_mensual,
        'estado': financiamiento.estado,
        'motivo_respaldo': motivo,
        'respaldado_en': datetime.now().isoformat(),
    }
