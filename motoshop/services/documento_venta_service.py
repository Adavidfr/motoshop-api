"""Lógica de negocio de documentos de venta con archivos reales.

Plan de retiro de archivo_url_legacy (fases):
  1. Actual: legacy read-only; nuevos documentos exigen FileField.
  2. Migración de datos: copiar URLs internas válidas a archivos en storage.
  3. Deprecar campo en API y eliminar columna cuando no queden registros legacy.
"""

import os
import uuid
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404

from motoshop.services.constants import (
    DOCUMENTO_VENTA_EXTENSIONES,
    DOCUMENTO_VENTA_MAX_BYTES,
    DOCUMENTO_VENTA_MIME,
)
from motoshop.services.exceptions import BusinessError
from motoshop.services.notificacion_service import NotificacionService


def _extension_segura(nombre):
    _, ext = os.path.splitext(nombre.lower())
    return ext if ext in DOCUMENTO_VENTA_EXTENSIONES else None


def _ruta_almacenamiento(extension):
    return f'documentos_venta/{uuid.uuid4().hex}{extension}'


def _legacy_url_es_segura(url):
    """
    Solo rutas relativas bajo MEDIA; rechaza URLs externas arbitrarias.
    """
    if not url or not url.strip():
        return False
    url = url.strip()
    if url.startswith(('http://', 'https://', '//')):
        return False
    media_prefix = settings.MEDIA_URL.lstrip('/')
    path = url.lstrip('/')
    if path.startswith(media_prefix):
        return True
    if url.startswith('/') and not url.startswith('//'):
        return True
    if not url.startswith('/') and '..' not in url:
        return True
    return False


def _resolver_ruta_legacy(url):
    """Convierte URL legacy relativa a ruta en storage."""
    url = url.strip()
    if url.startswith(settings.MEDIA_URL):
        return url[len(settings.MEDIA_URL):].lstrip('/')
    parsed = urlparse(url)
    if parsed.path.startswith(settings.MEDIA_URL):
        return parsed.path[len(settings.MEDIA_URL):].lstrip('/')
    return url.lstrip('/')


class DocumentoVentaService:
    @classmethod
    def validar_archivo(cls, archivo):
        if not archivo:
            raise BusinessError('Debe adjuntar un archivo.', field='archivo')

        ext = _extension_segura(archivo.name)
        if not ext:
            raise BusinessError(
                f'Extensión no permitida. Permitidas: {sorted(DOCUMENTO_VENTA_EXTENSIONES)}.',
                field='archivo',
            )

        content_type = getattr(archivo, 'content_type', '') or ''
        if content_type and content_type not in DOCUMENTO_VENTA_MIME:
            raise BusinessError(
                f'Tipo MIME no permitido: {content_type}.',
                field='archivo',
            )

        if archivo.size > DOCUMENTO_VENTA_MAX_BYTES:
            raise BusinessError(
                f'El archivo excede el tamaño máximo de '
                f'{DOCUMENTO_VENTA_MAX_BYTES // (1024 * 1024)} MB.',
                field='archivo',
            )
        return ext, content_type or 'application/octet-stream'

    @classmethod
    def subir(cls, venta, tipo_documento, archivo, subido_por):
        ext, content_type = cls.validar_archivo(archivo)
        ruta = _ruta_almacenamiento(ext)
        nombre_guardado = default_storage.save(ruta, archivo)

        from motoshop.models import DocumentoVenta

        documento = DocumentoVenta.objects.create(
            id_venta=venta,
            tipo_documento=tipo_documento,
            archivo=nombre_guardado,
            nombre_original=archivo.name,
            tamano_bytes=archivo.size,
            content_type=content_type,
            subido_por=subido_por,
        )
        NotificacionService.documento_disponible(documento)
        return documento

    @classmethod
    def reemplazar_archivo(cls, documento, archivo, subido_por):
        ext, content_type = cls.validar_archivo(archivo)
        cls._eliminar_fisico(documento)

        ruta = _ruta_almacenamiento(ext)
        nombre_guardado = default_storage.save(ruta, archivo)

        documento.archivo = nombre_guardado
        documento.nombre_original = archivo.name
        documento.tamano_bytes = archivo.size
        documento.content_type = content_type
        documento.subido_por = subido_por
        documento.archivo_url_legacy = ''
        documento.save(update_fields=[
            'archivo', 'nombre_original', 'tamano_bytes', 'content_type',
            'subido_por', 'archivo_url_legacy',
        ])
        return documento

    @staticmethod
    def _eliminar_fisico(documento):
        if documento.archivo:
            try:
                default_storage.delete(documento.archivo.name)
            except Exception:
                pass

    @classmethod
    def eliminar(cls, documento):
        cls._eliminar_fisico(documento)
        documento.delete()

    @staticmethod
    def puede_descargar(documento, usuario):
        if usuario.is_staff:
            return True
        return documento.id_venta.id_usuario_cliente_id == usuario.id

    @classmethod
    def obtener_respuesta_descarga(cls, documento):
        """Devuelve FileResponse para archivo nuevo o legacy seguro."""
        if documento.archivo and documento.archivo.name:
            if default_storage.exists(documento.archivo.name):
                archivo = documento.archivo
                response = FileResponse(
                    archivo.open('rb'),
                    content_type=documento.content_type or 'application/octet-stream',
                )
                response['Content-Disposition'] = (
                    f'attachment; filename="{documento.nombre_original or "documento"}"'
                )
                return response
            raise BusinessError('El archivo no existe en el almacenamiento.')

        legacy = documento.archivo_url_legacy
        if legacy and _legacy_url_es_segura(legacy):
            ruta = _resolver_ruta_legacy(legacy)
            if default_storage.exists(ruta):
                response = FileResponse(
                    default_storage.open(ruta, 'rb'),
                    content_type=documento.content_type or 'application/octet-stream',
                )
                response['Content-Disposition'] = (
                    f'attachment; filename="{documento.nombre_original or "documento_legacy"}"'
                )
                return response
            raise BusinessError('El archivo legacy no existe en el almacenamiento.')

        raise BusinessError('Este documento no tiene archivo almacenado.')

    @staticmethod
    def obtener_archivo(documento):
        """Compatibilidad interna; preferir obtener_respuesta_descarga."""
        if documento.archivo and default_storage.exists(documento.archivo.name):
            return documento.archivo
        raise BusinessError('Este documento no tiene archivo almacenado.')
