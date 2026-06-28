from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Compra
from motoshop.serializers.compra import CompraSerializer
from motoshop.permissions import IsAdminOrReadOnly
from motoshop.filters import CompraFilter
from motoshop.pagination import StandardPagination


class CompraViewSet(viewsets.ModelViewSet):
    queryset = Compra.objects.select_related(
        'proveedor',
        'moto',
        'repuesto'
    ).all()

    serializer_class = CompraSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CompraFilter

    search_fields = [
        'proveedor__nombre',
        'moto__modelo',
        'repuesto__nombre',
        'estado',
    ]

    ordering_fields = [
        'fecha_compra',
        'cantidad',
        'precio_unitario',
        'subtotal',
        'estado',
    ]

    ordering = ['-fecha_compra']

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = Compra.objects.all()

        return Response({
            'total': qs.count(),
            'pendientes': qs.filter(estado__iexact='Pendiente').count(),
            'recibidas': qs.filter(estado__iexact='Recibida').count(),
            'canceladas': qs.filter(estado__iexact='Cancelada').count(),
            'detail': [
                {
                    'id_compra': c.id_compra,
                    'proveedor': c.proveedor.nombre if c.proveedor else None,
                    'moto': str(c.moto) if c.moto else None,
                    'repuesto': str(c.repuesto) if c.repuesto else None,
                    'cantidad': c.cantidad,
                    'subtotal': c.subtotal,
                    'estado': c.estado,
                    'fecha_compra': c.fecha_compra,
                }
                for c in qs.order_by('-fecha_compra')
            ],
        })