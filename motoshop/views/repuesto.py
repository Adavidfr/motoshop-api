from rest_framework import viewsets
from motoshop.models.repuesto import Repuesto
from motoshop.serializers.repuesto import RepuestoSerializer
from motoshop.permissions import IsAdminOrReadOnly

class RepuestoViewSet(viewsets.ModelViewSet):
    queryset = Repuesto.objects.all()
    serializer_class = RepuestoSerializer
    permission_classes = [IsAdminOrReadOnly]
