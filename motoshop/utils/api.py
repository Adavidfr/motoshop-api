"""Utilidades para respuestas HTTP desde servicios."""

from rest_framework import status
from rest_framework.response import Response

from motoshop.services.exceptions import BusinessError


def respuesta_error_servicio(exc):
    if isinstance(exc, BusinessError):
        data = exc.as_dict()
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    raise exc
