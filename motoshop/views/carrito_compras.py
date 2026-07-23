# motoshop/views/carrito_compras.py

from rest_framework import viewsets, status

from rest_framework.decorators import action

from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response

from rest_framework.filters import OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend



from motoshop.models import CarritoCompras

from motoshop.serializers.carrito_compras import CarritoComprasSerializer

from motoshop.serializers.item_carrito import AddItemCarritoSerializer

from motoshop.pagination import StandardPagination

from motoshop.filters import CarritoFilter

from motoshop.permissions import IsClientWriteOrStaffReadOnly

from motoshop.services import BusinessError, CarritoService

from motoshop.utils.api import respuesta_error_servicio





class CarritoComprasViewSet(viewsets.ModelViewSet):

    """

    ViewSet CRUD de carrito_compras (tabla: carrito_compras).



    Clientes: CRUD de carrito propio, add-item, vaciar y remove-item.

    Administradores: solo lectura (consulta/revisión).

    """

    serializer_class   = CarritoComprasSerializer

    permission_classes = [IsAuthenticated, IsClientWriteOrStaffReadOnly]

    pagination_class   = StandardPagination

    filter_backends    = [DjangoFilterBackend, OrderingFilter]

    filterset_class    = CarritoFilter

    ordering_fields    = ['fecha_creacion']

    ordering           = ['-fecha_creacion']

    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']



    def get_queryset(self):

        if self.request.user.is_staff:

            return (

                CarritoCompras.objects

                .select_related('id_usuario_cliente')

                .prefetch_related('items')

                .all()

            )

        return (

            CarritoCompras.objects

            .filter(id_usuario_cliente=self.request.user)

            .prefetch_related('items')

        )



    def create(self, request, *args, **kwargs):
        carrito, created = CarritoService.obtener_o_crear_activo(request.user)
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(CarritoComprasSerializer(carrito).data, status=code)

    def perform_create(self, serializer):
        pass

    @action(detail=False, methods=['get'], url_path='activo')

    def activo(self, request):

        """Devuelve el carrito activo del usuario autenticado."""

        carrito = CarritoService.obtener_activo(request.user)

        if not carrito:

            carrito, _ = CarritoService.obtener_o_crear_activo(request.user)

        return Response(CarritoComprasSerializer(carrito).data)



    @action(detail=True, methods=['post'], url_path='add-item')

    def add_item(self, request, pk=None):

        carrito = self.get_object()

        serializer = AddItemCarritoSerializer(

            data=request.data,

            context={'carrito': carrito, 'request': request},

        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data



        try:

            CarritoService.agregar_item(

                carrito,

                request.user,

                id_moto=data.get('id_moto'),

                id_repuesto=data.get('id_repuesto'),

                cantidad=data['cantidad'],

            )

        except BusinessError as exc:

            return respuesta_error_servicio(exc)



        carrito_actualizado = self.get_queryset().get(pk=carrito.pk)

        return Response(CarritoComprasSerializer(carrito_actualizado).data)



    @action(detail=True, methods=['delete'], url_path=r'remove-item/(?P<item_id>[^/.]+)')

    def remove_item(self, request, pk=None, item_id=None):

        carrito = self.get_object()

        try:

            CarritoService.eliminar_item(carrito, request.user, item_id)

        except BusinessError as exc:

            status_code = (

                status.HTTP_404_NOT_FOUND

                if 'no encontrado' in exc.message.lower()

                else status.HTTP_400_BAD_REQUEST

            )

            return Response(exc.as_dict(), status=status_code)



        carrito_actualizado = self.get_queryset().get(pk=carrito.pk)

        return Response(CarritoComprasSerializer(carrito_actualizado).data)



    @action(detail=True, methods=['post'], url_path='vaciar')

    def vaciar(self, request, pk=None):

        carrito = self.get_object()

        try:

            CarritoService.vaciar(carrito, request.user)

        except BusinessError as exc:

            return respuesta_error_servicio(exc)



        carrito_actualizado = self.get_queryset().get(pk=carrito.pk)

        return Response(CarritoComprasSerializer(carrito_actualizado).data)


