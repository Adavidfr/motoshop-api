from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from motoshop.models.categoria_moto import CategoriaMoto
from motoshop.serializers.categoria_moto import CategoriaMotoSerializer
from motoshop.permissions import IsAdminOrReadOnly

class CategoriaMotoViewSet(viewsets.ModelViewSet):
    queryset = CategoriaMoto.objects.all()
    serializer_class = CategoriaMotoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'estado']
