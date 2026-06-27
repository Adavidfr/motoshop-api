from rest_framework import viewsets
from motoshop.models.movimiento_inventario import MovimientoInventario
from motoshop.serializers.movimiento_inventario import MovimientoInventarioSerializer
from motoshop.permissions import IsAdminOrVendedor

class MovimientoInventarioViewSet(viewsets.ModelViewSet):
    queryset = MovimientoInventario.objects.all()
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [IsAdminOrVendedor]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
