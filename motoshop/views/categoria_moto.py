from rest_framework import viewsets
from motoshop.models.categoria_moto import CategoriaMoto
from motoshop.serializers.categoria_moto import CategoriaMotoSerializer
from motoshop.permissions import IsAdminOrReadOnly

class CategoriaMotoViewSet(viewsets.ModelViewSet):
    queryset = CategoriaMoto.objects.all()
    serializer_class = CategoriaMotoSerializer
    permission_classes = [IsAdminOrReadOnly]
