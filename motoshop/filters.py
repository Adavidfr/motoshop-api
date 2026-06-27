# motoshop/filters.py
import django_filters
from motoshop.models import CarritoCompras, ItemCarrito, Pedido, Venta, Financiamiento


class CarritoFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name='fecha_creacion', lookup_expr='date__gte')
    to_date   = django_filters.DateFilter(field_name='fecha_creacion', lookup_expr='date__lte')

    class Meta:
        model  = CarritoCompras
        fields = ['estado']


class ItemCarritoFilter(django_filters.FilterSet):
    class Meta:
        model  = ItemCarrito
        fields = ['id_carrito', 'id_moto', 'id_repuesto']


class PedidoFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name='fecha_pedido', lookup_expr='date__gte')
    to_date   = django_filters.DateFilter(field_name='fecha_pedido', lookup_expr='date__lte')

    class Meta:
        model  = Pedido
        fields = ['estado']


class VentaFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name='fecha_venta', lookup_expr='date__gte')
    to_date   = django_filters.DateFilter(field_name='fecha_venta', lookup_expr='date__lte')

    class Meta:
        model  = Venta
        fields = ['estado']


class FinanciamientoFilter(django_filters.FilterSet):
    monto_min          = django_filters.NumberFilter(field_name='monto_financiado', lookup_expr='gte')
    monto_max          = django_filters.NumberFilter(field_name='monto_financiado', lookup_expr='lte')
    entidad_financiera = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model  = Financiamiento
        fields = ['estado', 'id_venta']
