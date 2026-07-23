# motoshop/views/pago.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count

from motoshop.models import Pago
from motoshop.serializers.pago import PagoSerializer, PagoCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import PagoFilter
from motoshop.permissions import filter_queryset_by_venta_owner
from motoshop.services import BusinessError, PagoService
from motoshop.utils.api import respuesta_error_servicio


class PagoViewSet(viewsets.ModelViewSet):
    """Pagos conectados a PagoService."""
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = PagoFilter
    search_fields      = ['referencia', 'metodo_pago', 'tipo_pago']
    ordering_fields    = ['id_pago', 'monto', 'fecha_pago']
    ordering           = ['-fecha_pago']
    http_method_names  = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        qs = Pago.objects.select_related(
            'id_venta', 'id_venta__id_usuario_cliente', 'procesado_por', 'id_financiamiento',
        ).all()
        return filter_queryset_by_venta_owner(qs, self.request.user)

    def get_permissions(self):
        if self.action in ('create', 'stats'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return PagoCreateSerializer
        return PagoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        financiamiento = data.get('id_financiamiento')
        try:
            pago = PagoService.registrar_pago(
                venta=data['id_venta'],
                monto=data['monto'],
                metodo_pago=data['metodo_pago'],
                procesado_por=request.user,
                tipo_pago=data.get('tipo_pago', 'contado'),
                id_financiamiento=(
                    financiamiento.pk if financiamiento is not None else None
                ),
                estado=data.get('estado', 'completado'),
                referencia=data.get('referencia', ''),
                comprobante=data.get('comprobante'),
            )
        except BusinessError as exc:
            return respuesta_error_servicio(exc)
        return Response(PagoSerializer(pago).data, status=201)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = Pago.objects.all()
        totales = qs.aggregate(total_pagos=Count('id_pago'), monto_total=Sum('monto'))
        por_estado = {e: qs.filter(estado=e).count() for e, _ in Pago.ESTADO_CHOICES}
        por_metodo = {m: qs.filter(metodo_pago=m).count() for m, _ in Pago.METODO_CHOICES}
        return Response({
            'total_pagos': totales['total_pagos'],
            'monto_total': float(totales['monto_total'] or 0),
            'por_estado': por_estado,
            'por_metodo': por_metodo,
        })
