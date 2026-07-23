from rest_framework import viewsets, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models.movimiento_inventario import MovimientoInventario
from motoshop.serializers.movimiento_inventario import MovimientoInventarioSerializer
from motoshop.services import BusinessError, InventarioService
from motoshop.utils.api import respuesta_error_servicio


class MovimientoInventarioViewSet(viewsets.ModelViewSet):
    queryset = MovimientoInventario.objects.all()
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['tipo_movimiento', 'descripcion']
    ordering_fields = ['fecha_movimiento', 'cantidad']
    http_method_names = ['get', 'post', 'head', 'options']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        moto = data.get('moto')
        repuesto = data.get('repuesto')
        cantidad = abs(data['cantidad'])
        tipo = data.get('tipo_movimiento', 'ajuste_manual')
        desc = data.get('descripcion', '')
        try:
            if data['cantidad'] >= 0:
                mov = InventarioService.aumentar_stock(
                    cantidad, request.user,
                    id_moto=moto.pk if moto else None,
                    id_repuesto=repuesto.pk if repuesto else None,
                    tipo_movimiento=tipo,
                    descripcion=desc,
                )
            else:
                mov = InventarioService.disminuir_stock(
                    cantidad, request.user,
                    id_moto=moto.pk if moto else None,
                    id_repuesto=repuesto.pk if repuesto else None,
                    tipo_movimiento=tipo,
                    descripcion=desc,
                )
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(
            MovimientoInventarioSerializer(mov).data,
            status=status.HTTP_201_CREATED,
        )
