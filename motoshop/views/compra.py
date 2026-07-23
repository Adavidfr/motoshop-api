from rest_framework import viewsets, status

from rest_framework.decorators import action

from rest_framework.permissions import IsAdminUser

from rest_framework.response import Response

from rest_framework.filters import SearchFilter, OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend



from motoshop.models import Compra

from motoshop.serializers.compra import CompraSerializer

from motoshop.permissions import IsAdminOrReadOnly

from motoshop.filters import CompraFilter

from motoshop.pagination import StandardPagination

from motoshop.services import BusinessError, CompraService

from motoshop.utils.api import respuesta_error_servicio





class CompraViewSet(viewsets.ModelViewSet):

    queryset = Compra.objects.select_related('proveedor', 'moto', 'repuesto').all()

    serializer_class = CompraSerializer

    permission_classes = [IsAdminOrReadOnly]

    pagination_class = StandardPagination

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_class = CompraFilter

    search_fields = ['proveedor__nombre', 'moto__modelo', 'repuesto__nombre', 'estado']

    ordering_fields = ['fecha_compra', 'cantidad', 'precio_unitario', 'subtotal', 'estado']

    ordering = ['-fecha_compra']



    def perform_create(self, serializer):

        serializer.save()



    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        nuevo_estado = serializer.validated_data.get('estado', instance.estado)
        if nuevo_estado != instance.estado:
            try:
                instance = CompraService.cambiar_estado(instance, nuevo_estado, request.user)
            except BusinessError as exc:
                return respuesta_error_servicio(exc)
            return Response(CompraSerializer(instance).data)
        serializer.save()
        return Response(CompraSerializer(instance).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser], url_path='recibir')

    def recibir(self, request, pk=None):

        compra = self.get_object()

        try:

            compra = CompraService.cambiar_estado(compra, 'Recibida', request.user)

        except BusinessError as exc:

            return respuesta_error_servicio(exc)

        return Response(CompraSerializer(compra).data)



    @action(detail=False, methods=['get'], url_path='stats')

    def stats(self, request):

        qs = Compra.objects.all()

        return Response({

            'total': qs.count(),

            'pendientes': qs.filter(estado__iexact='Pendiente').count(),

            'recibidas': qs.filter(estado__iexact='Recibida').count(),

            'canceladas': qs.filter(estado__iexact='Cancelada').count(),

        })


