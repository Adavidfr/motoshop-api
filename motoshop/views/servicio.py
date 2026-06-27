from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Servicio
from motoshop.serializers.servicio import ServicioSerializer
from motoshop.permissions import IsAdminOrReadOnly
from motoshop.filters import ServicioFilter
from motoshop.pagination import StandardPagination


class ServicioViewSet(viewsets.ModelViewSet):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ServicioFilter
    search_fields = ['nombre', 'descripcion']
    ordering_fields = [
        'nombre',
        'precio_base',
        'tiempo_estimado_minutos',
        'fecha_creacion',
    ]
    ordering = ['nombre']

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = Servicio.objects.all()

        return Response({
            'total': qs.count(),
            'activos': qs.filter(estado=True).count(),
            'inactivos': qs.filter(estado=False).count(),
            'detail': [
                {
                    'id': s.id,
                    'nombre': s.nombre,
                    'precio_base': s.precio_base,
                    'tiempo_estimado_minutos': s.tiempo_estimado_minutos,
                    'estado': s.estado,
                }
                for s in qs.order_by('nombre')
            ],
        })