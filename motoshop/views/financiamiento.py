# motoshop/views/financiamiento.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Avg

from motoshop.models import Financiamiento
from motoshop.serializers.financiamiento import (
    FinanciamientoSerializer,
    FinanciamientoCreateSerializer,
)
from motoshop.pagination import StandardPagination
from motoshop.filters    import FinanciamientoFilter


class FinanciamientoViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de financiamientos.
    Solo accesible para staff/admin.

    Endpoints generados:
      GET    /financiamientos/              → listar todos
      POST   /financiamientos/              → crear
      GET    /financiamientos/<id>/         → detalle
      PATCH  /financiamientos/<id>/         → editar
      DELETE /financiamientos/<id>/         → eliminar

    Filtros disponibles:
      ?estado=activo
      ?id_venta=<id>
      ?entidad_financiera=<nombre>
      ?monto_min=<valor>
      ?monto_max=<valor>

    Acciones custom:
      GET  /financiamientos/stats/          → estadísticas globales
    """
    permission_classes = [IsAdminUser]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = FinanciamientoFilter
    search_fields      = ['entidad_financiera']
    ordering_fields    = ['id_financiamiento', 'monto_financiado', 'plazo_meses', 'cuota_mensual']
    ordering           = ['-id_financiamiento']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Financiamiento.objects.select_related('id_venta__id_pedido').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return FinanciamientoCreateSerializer
        return FinanciamientoSerializer

    # ------------------------------------------------------------------ #
    #  Action: estadísticas                                                #
    # ------------------------------------------------------------------ #
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Resumen de financiamientos: totales por estado, montos y promedios.
        Solo staff.
        """
        qs = Financiamiento.objects.all()
        totales = qs.aggregate(
            total_financiamientos = Count('id_financiamiento'),
            monto_total           = Sum('monto_financiado'),
            monto_promedio        = Avg('monto_financiado'),
            cuota_promedio        = Avg('cuota_mensual'),
            plazo_promedio        = Avg('plazo_meses'),
        )
        por_estado = {
            e: qs.filter(estado=e).count()
            for e, _ in Financiamiento.ESTADO_CHOICES
        }
        return Response({
            'total_financiamientos': totales['total_financiamientos'],
            'monto_total':           float(totales['monto_total'] or 0),
            'monto_promedio':        round(float(totales['monto_promedio'] or 0), 2),
            'cuota_promedio':        round(float(totales['cuota_promedio'] or 0), 2),
            'plazo_promedio_meses':  round(float(totales['plazo_promedio'] or 0), 1),
            'por_estado':            por_estado,
        })
