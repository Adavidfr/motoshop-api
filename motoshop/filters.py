import django_filters
from motoshop.models import Proveedor, Servicio, Compra, Mantenimiento
from motoshop.models.repuesto_mantenimiento import RepuestoMantenimiento
from motoshop.models import CarritoCompras, ItemCarrito, Pedido, Venta, Financiamiento
from motoshop.models import (
    Pago, Factura, Garantia, Seguro,
    Notificacion, DocumentoVenta, HistorialEstadoVenta, Devolucion,
)


class ProveedorFilter(django_filters.FilterSet):
    nombre = django_filters.CharFilter(lookup_expr='icontains')
    contacto = django_filters.CharFilter(lookup_expr='icontains')
    correo = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Proveedor
        fields = ['estado']
        

class ServicioFilter(django_filters.FilterSet):
    nombre = django_filters.CharFilter(lookup_expr='icontains')
    descripcion = django_filters.CharFilter(lookup_expr='icontains')
    precio_base = django_filters.NumberFilter()

    class Meta:
        model = Servicio
        fields = ['estado']
        
class CompraFilter(django_filters.FilterSet):
    estado = django_filters.CharFilter(lookup_expr='icontains')

    fecha_compra = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Compra
        fields = [
            'proveedor',
            'moto',
            'repuesto',
            'estado',
            'fecha_compra',
        ]
        
class MantenimientoFilter(django_filters.FilterSet):
    estado = django_filters.CharFilter(lookup_expr='icontains')
    fecha_registro = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Mantenimiento
        fields = [
            'moto',
            'usuario_cliente',
            'servicio',
            'estado',
            'fecha_registro',
        ]
    
class RepuestoMantenimientoFilter(django_filters.FilterSet):

    class Meta:
        model = RepuestoMantenimiento
        fields = [
            'mantenimiento',
            'repuesto',
        ]


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


class PagoFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name='fecha_pago', lookup_expr='date__gte')
    to_date   = django_filters.DateFilter(field_name='fecha_pago', lookup_expr='date__lte')

    class Meta:
        model  = Pago
        fields = ['estado', 'metodo_pago', 'id_venta']


class FacturaFilter(django_filters.FilterSet):
    numero_factura = django_filters.CharFilter(lookup_expr='icontains')
    id_venta = django_filters.NumberFilter(field_name='id_pago__id_venta')
    id_pago = django_filters.NumberFilter(field_name='id_pago')

    class Meta:
        model  = Factura
        fields = ['id_venta', 'id_pago']


class GarantiaFilter(django_filters.FilterSet):
    class Meta:
        model  = Garantia
        fields = ['estado', 'id_venta']


class SeguroFilter(django_filters.FilterSet):
    aseguradora = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model  = Seguro
        fields = ['estado', 'id_venta']


class NotificacionFilter(django_filters.FilterSet):
    class Meta:
        model  = Notificacion
        fields = ['leido', 'id_usuario']


class DocumentoVentaFilter(django_filters.FilterSet):
    class Meta:
        model  = DocumentoVenta
        fields = ['tipo_documento', 'id_venta']


class HistorialEstadoVentaFilter(django_filters.FilterSet):
    class Meta:
        model  = HistorialEstadoVenta
        fields = ['id_venta', 'estado_nuevo']


class DevolucionFilter(django_filters.FilterSet):
    class Meta:
        model  = Devolucion
        fields = ['estado', 'id_venta']
