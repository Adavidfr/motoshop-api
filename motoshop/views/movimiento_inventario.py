from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from motoshop.models.movimiento_inventario import MovimientoInventario
from motoshop.serializers.movimiento_inventario import MovimientoInventarioSerializer
from motoshop.permissions import IsAdminOrVendedor

class MovimientoInventarioViewSet(viewsets.ModelViewSet):
    queryset = MovimientoInventario.objects.all()
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [IsAdminOrVendedor]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['tipo_movimiento', 'descripcion']
    ordering_fields = ['fecha_movimiento', 'cantidad']

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
