"""Lógica de negocio de seguros — numeración automática de pólizas."""

import re
from decimal import Decimal

from django.db import IntegrityError, transaction

from motoshop.models import Seguro, Venta
from motoshop.services.exceptions import BusinessError

POLIZA_PREFIX = 'POL'
POLIZA_RE = re.compile(r'^POL-(\d{4})-(\d{6})$')
MAX_REINTENTOS_UNICIDAD = 8


class SeguroService:
    """Creación de seguros con numero_poliza generado por el servidor."""

    @classmethod
    def _formatear_poliza(cls, anio: int, secuencia: int) -> str:
        return f'{POLIZA_PREFIX}-{anio}-{secuencia:06d}'

    @classmethod
    def _siguiente_secuencia(cls, anio: int) -> int:
        """
        Obtiene el siguiente correlativo del año a partir del último
        numero_poliza con formato POL-YYYY-######.
        Requiere estar dentro de transaction.atomic() + select_for_update.
        """
        prefijo = f'{POLIZA_PREFIX}-{anio}-'
        candidatos = (
            Seguro.objects
            .select_for_update()
            .filter(numero_poliza__startswith=prefijo)
            .order_by('-numero_poliza')
            .values_list('numero_poliza', flat=True)
        )
        for numero in candidatos:
            match = POLIZA_RE.fullmatch(numero)
            if match and int(match.group(1)) == anio:
                return int(match.group(2)) + 1
        return 1

    @classmethod
    def generar_numero_poliza(cls, fecha_inicio) -> str:
        """Año = fecha_inicio (inicio de cobertura). Sin created_at en el modelo."""
        anio = fecha_inicio.year
        secuencia = cls._siguiente_secuencia(anio)
        return cls._formatear_poliza(anio, secuencia)

    @classmethod
    def crear(
        cls,
        *,
        venta,
        aseguradora: str,
        tipo_cobertura: str,
        fecha_inicio,
        fecha_fin,
        costo_anual,
        estado: str = 'activo',
    ) -> Seguro:
        if isinstance(venta, int):
            try:
                venta = Venta.objects.get(pk=venta)
            except Venta.DoesNotExist as exc:
                raise BusinessError('La venta no existe.', field='id_venta') from exc

        if not aseguradora or not str(aseguradora).strip():
            raise BusinessError('La aseguradora es obligatoria.', field='aseguradora')
        if not tipo_cobertura or not str(tipo_cobertura).strip():
            raise BusinessError('El tipo de cobertura es obligatorio.', field='tipo_cobertura')
        if fecha_fin <= fecha_inicio:
            raise BusinessError(
                'La fecha de fin debe ser posterior a la fecha de inicio.',
                field='fecha_fin',
            )

        costo = Decimal(str(costo_anual))
        if costo < 0:
            raise BusinessError(
                'El costo anual no puede ser negativo.',
                field='costo_anual',
            )

        last_error: Exception | None = None
        for _ in range(MAX_REINTENTOS_UNICIDAD):
            try:
                with transaction.atomic():
                    numero_poliza = cls.generar_numero_poliza(fecha_inicio)
                    return Seguro.objects.create(
                        id_venta=venta,
                        aseguradora=str(aseguradora).strip(),
                        numero_poliza=numero_poliza,
                        tipo_cobertura=str(tipo_cobertura).strip(),
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin,
                        costo_anual=costo,
                        estado=estado or 'activo',
                    )
            except IntegrityError as exc:
                last_error = exc
                continue

        raise BusinessError(
            'No se pudo generar un número de póliza único. Intente nuevamente.',
            field='numero_poliza',
        ) from last_error
