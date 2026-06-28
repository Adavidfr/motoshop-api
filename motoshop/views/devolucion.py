# motoshop/views/devolucion.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum

from motoshop.models import Devolucion
from motoshop.serializers.devolucion import DevolucionSerializer, DevolucionCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import DevolucionFilter


class DevolucionViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de devoluciones.
    Solo accesible para staff/admin.

    Endpoints generados:
      GET    /devoluciones/          → listar todas
      POST   /devoluciones/          → registrar solicitud
      GET    /devoluciones/<id>/     → detalle
      PATCH  /devoluciones/<id>/     → editar (cambiar estado, fecha_resolucion, etc.)
      DELETE /devoluciones/<id>/     → eliminar

    Filtros disponibles:
      ?estado=solicitada
      ?id_venta=<id>

    Acciones custom:
      GET  /devoluciones/stats/      → estadísticas globales
    """
    permission_classes = [IsAdminUser]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = DevolucionFilter
    search_fields      = ['motivo']
    ordering_fields    = ['id_devolucion', 'monto_devolucion', 'fecha_solicitud']
    ordering           = ['-fecha_solicitud']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Devolucion.objects.select_related('id_venta').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return DevolucionCreateSerializer
        return DevolucionSerializer

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Resumen de devoluciones: totales por estado y monto devuelto."""
        qs = Devolucion.objects.all()
        totales = qs.aggregate(
            total_devoluciones = Count('id_devolucion'),
            monto_total        = Sum('monto_devolucion'),
        )
        por_estado = {
            e: qs.filter(estado=e).count()
            for e, _ in Devolucion.ESTADO_CHOICES
        }
        return Response({
            'total_devoluciones': totales['total_devoluciones'],
            'monto_total':        float(totales['monto_total'] or 0),
            'por_estado':         por_estado,
        })
