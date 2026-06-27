from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Mantenimiento
from motoshop.serializers.mantenimiento import MantenimientoSerializer
from motoshop.permissions import IsAdminOrReadOnly
from motoshop.filters import MantenimientoFilter
from motoshop.pagination import StandardPagination


class MantenimientoViewSet(viewsets.ModelViewSet):
    queryset = Mantenimiento.objects.select_related(
        'moto',
        'usuario_cliente',
        'servicio',
    ).all()

    serializer_class = MantenimientoSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MantenimientoFilter

    search_fields = [
        'moto__modelo',
        'usuario_cliente__username',
        'usuario_cliente__email',
        'servicio__nombre',
        'diagnostico_inicial',
        'estado',
    ]

    ordering_fields = [
        'fecha_registro',
        'kilometraje_actual',
        'costo_final',
        'estado',
    ]

    ordering = ['-fecha_registro']

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = Mantenimiento.objects.all()

        return Response({
            'total': qs.count(),
            'pendientes': qs.filter(estado__iexact='Pendiente').count(),
            'en_proceso': qs.filter(estado__iexact='En proceso').count(),
            'finalizados': qs.filter(estado__iexact='Finalizado').count(),
            'cancelados': qs.filter(estado__iexact='Cancelado').count(),
            'detail': [
                {
                    'id_mantenimiento': m.id_mantenimiento,
                    'moto': str(m.moto),
                    'usuario_cliente': m.usuario_cliente.username,
                    'servicio': m.servicio.nombre,
                    'kilometraje_actual': m.kilometraje_actual,
                    'costo_final': m.costo_final,
                    'estado': m.estado,
                    'fecha_registro': m.fecha_registro,
                }
                for m in qs.order_by('-fecha_registro')
            ],
        })