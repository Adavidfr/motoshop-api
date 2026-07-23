from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from motoshop.models.moto import Moto
from motoshop.serializers.moto import MotoSerializer
from motoshop.permissions import IsAdminOrReadOnly

class MotoViewSet(viewsets.ModelViewSet):
    queryset = Moto.objects.all().order_by('id_moto')
    serializer_class = MotoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['modelo', 'color', 'marca__nombre', 'categoria__nombre']
    ordering_fields = ['id_moto', 'precio', 'anio', 'stock', 'modelo']
    ordering = ['id_moto']
