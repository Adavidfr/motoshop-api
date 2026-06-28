from rest_framework import viewsets
from motoshop.models.marca import Marca
from motoshop.serializers.marca import MarcaSerializer
from motoshop.permissions import IsAdminOrReadOnly

class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAdminOrReadOnly]
