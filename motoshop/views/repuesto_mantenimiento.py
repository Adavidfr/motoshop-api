from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import RepuestoMantenimiento
from motoshop.serializers.repuesto_mantenimiento import RepuestoMantenimientoSerializer
from motoshop.permissions import IsAdminOrReadOnly
from motoshop.filters import RepuestoMantenimientoFilter
from motoshop.pagination import StandardPagination


class RepuestoMantenimientoViewSet(viewsets.ModelViewSet):
    queryset = RepuestoMantenimiento.objects.select_related(
        'mantenimiento',
        'repuesto'
    ).all()

    serializer_class = RepuestoMantenimientoSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RepuestoMantenimientoFilter

    search_fields = [
        'repuesto__nombre',
    ]

    ordering_fields = [
        'cantidad',
        'precio_unitario',
        'subtotal',
    ]

    ordering = ['id_repuesto_mantenimiento']

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = RepuestoMantenimiento.objects.all()

        return Response({
            'total': qs.count(),
            'detail': [
                {
                    'id': r.id_repuesto_mantenimiento,
                    'mantenimiento': r.mantenimiento.id_mantenimiento,
                    'repuesto': r.repuesto.nombre,
                    'cantidad': r.cantidad,
                    'subtotal': r.subtotal,
                }
                for r in qs
            ],
        })