# motoshop/views/pago.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count

from motoshop.models import Pago
from motoshop.serializers.pago import PagoSerializer, PagoCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import PagoFilter


class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de pagos.
    Solo accesible para staff/admin.

    Endpoints generados:
      GET    /pagos/          → listar todos
      POST   /pagos/          → registrar pago
      GET    /pagos/<id>/     → detalle
      PATCH  /pagos/<id>/     → editar
      DELETE /pagos/<id>/     → eliminar

    Filtros disponibles:
      ?estado=completado
      ?id_venta=<id>
      ?metodo_pago=<método>

    Acciones custom:
      GET  /pagos/stats/      → estadísticas globales
    """
    permission_classes = [IsAdminUser]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = PagoFilter
    search_fields      = ['referencia', 'metodo_pago']
    ordering_fields    = ['id_pago', 'monto', 'fecha_pago']
    ordering           = ['-fecha_pago']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Pago.objects.select_related('id_venta').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return PagoCreateSerializer
        return PagoSerializer

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Resumen de pagos: totales por estado y método de pago."""
        qs = Pago.objects.all()
        totales = qs.aggregate(
            total_pagos  = Count('id_pago'),
            monto_total  = Sum('monto'),
        )
        por_estado = {
            e: qs.filter(estado=e).count()
            for e, _ in Pago.ESTADO_CHOICES
        }
        por_metodo = {
            m: qs.filter(metodo_pago=m).count()
            for m, _ in Pago.METODO_CHOICES
        }
        return Response({
            'total_pagos':  totales['total_pagos'],
            'monto_total':  float(totales['monto_total'] or 0),
            'por_estado':   por_estado,
            'por_metodo':   por_metodo,
        })
