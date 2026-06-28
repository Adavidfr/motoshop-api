from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from motoshop.models.repuesto import Repuesto
from motoshop.serializers.repuesto import RepuestoSerializer
from motoshop.permissions import IsAdminOrReadOnly

class RepuestoViewSet(viewsets.ModelViewSet):
    queryset = Repuesto.objects.all()
    serializer_class = RepuestoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nombre', 'sku', 'descripcion']
    ordering_fields = ['precio_venta', 'costo', 'stock', 'nombre']
