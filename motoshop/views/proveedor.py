from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Proveedor
from motoshop.serializers.proveedor import ProveedorSerializer
from motoshop.permissions import IsAdminOrReadOnly
from motoshop.filters import ProveedorFilter
from motoshop.pagination import StandardPagination


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProveedorFilter
    search_fields = ['nombre', 'contacto', 'correo', 'telefono']
    ordering_fields = ['nombre', 'estado']
    ordering = ['nombre']

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = Proveedor.objects.all()

        return Response({
            'total': qs.count(),
            'activos': qs.filter(estado=True).count(),
            'inactivos': qs.filter(estado=False).count(),
            'detail': [
                {
                    'id': p.id,
                    'nombre': p.nombre,
                    'contacto': p.contacto,
                    'telefono': p.telefono,
                    'correo': p.correo,
                    'estado': p.estado,
                }
                for p in qs.order_by('nombre')
            ],
        })