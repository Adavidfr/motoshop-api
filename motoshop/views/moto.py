from rest_framework import viewsets
from motoshop.models.moto import Moto
from motoshop.serializers.moto import MotoSerializer
from motoshop.permissions import IsAdminOrReadOnly

class MotoViewSet(viewsets.ModelViewSet):
    queryset = Moto.objects.all()
    serializer_class = MotoSerializer
    permission_classes = [IsAdminOrReadOnly]
